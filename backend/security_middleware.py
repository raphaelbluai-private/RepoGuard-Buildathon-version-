from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

_PROTECTED_PATHS = {
    "/v1/repoguard/verify",
    "/v1/repoguard/safe-to-ship",
    "/v1/repoguard/scan",
    "/v1/repoguard/explain",
    "/v1/repoguard/attest",
}


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value < 1:
        raise RuntimeError(f"{name} must be at least 1")
    return value


def _allowed_origins() -> list[str]:
    configured = os.environ.get(
        "REPOGUARD_ALLOWED_ORIGINS",
        os.environ.get("REPOGUARD_CORS_ORIGINS", ""),
    )
    values = [value.strip().rstrip("/") for value in configured.split(",")]
    origins = [value for value in values if value]
    if "*" in origins:
        raise RuntimeError("REPOGUARD_ALLOWED_ORIGINS cannot contain a wildcard")
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError("REPOGUARD_ALLOWED_ORIGINS must contain exact HTTPS origins")
    return origins


@dataclass(frozen=True)
class SecuritySettings:
    max_body_bytes: int
    max_concurrent_scans: int
    client_requests_per_minute: int
    repository_scans_per_hour: int


class SecurityState:
    def __init__(self, settings: SecuritySettings):
        self.settings = settings
        self.semaphore = threading.BoundedSemaphore(settings.max_concurrent_scans)
        self.lock = threading.Lock()
        self.client_windows: dict[str, deque[float]] = defaultdict(deque)
        self.repository_windows: dict[str, deque[float]] = defaultdict(deque)

    def consume(self, client: str, repository: str | None) -> str | None:
        now = time.monotonic()
        with self.lock:
            client_window = self.client_windows[client]
            while client_window and client_window[0] <= now - 60:
                client_window.popleft()
            if len(client_window) >= self.settings.client_requests_per_minute:
                return "CLIENT_RATE_LIMIT_EXCEEDED"
            if repository:
                repo_window = self.repository_windows[repository.lower()]
                while repo_window and repo_window[0] <= now - 3600:
                    repo_window.popleft()
                if len(repo_window) >= self.settings.repository_scans_per_hour:
                    return "REPOSITORY_QUOTA_EXCEEDED"
                repo_window.append(now)
            client_window.append(now)
        return None


class SecurityMiddleware:
    def __init__(self, app: Any, state: SecurityState):
        self.app = app
        self.state = state

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        protected = scope.get("method") == "POST" and path in _PROTECTED_PATHS
        acquired = False
        body = b""

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                security_names = {
                    b"x-content-type-options",
                    b"x-frame-options",
                    b"referrer-policy",
                    b"content-security-policy",
                    b"permissions-policy",
                }
                headers = [
                    (name, value)
                    for name, value in headers
                    if name.lower() not in security_names
                ]
                api_csp = b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                static_csp = (
                    b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                    b"img-src 'self' data:; font-src 'self'; connect-src 'self'; "
                    b"frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
                )
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (
                            b"content-security-policy",
                            api_csp if path.startswith(("/api", "/v1")) else static_csp,
                        ),
                        (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                    ]
                )
                message["headers"] = headers
            await send(message)

        try:
            if protected:
                max_bytes = self.state.settings.max_body_bytes
                more = True
                while more:
                    message = await receive()
                    chunk = message.get("body", b"")
                    body += chunk
                    if len(body) > max_bytes:
                        await JSONResponse(
                            {"error": "REQUEST_BODY_TOO_LARGE"}, status_code=413
                        )(scope, receive, secure_send)
                        return
                    more = message.get("more_body", False)

                try:
                    payload = json.loads(body or b"{}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    payload = {}
                repository = payload.get("repo") if isinstance(payload, dict) else None
                client = str((scope.get("client") or ("unknown", 0))[0])
                quota_error = self.state.consume(client, repository if isinstance(repository, str) else None)
                if quota_error:
                    await JSONResponse({"error": quota_error}, status_code=429)(
                        scope, receive, secure_send
                    )
                    return

                acquired = self.state.semaphore.acquire(blocking=False)
                if not acquired:
                    await JSONResponse(
                        {"error": "SCAN_CAPACITY_EXHAUSTED"}, status_code=503
                    )(scope, receive, secure_send)
                    return

                delivered = False

                async def replay_receive():
                    nonlocal delivered
                    if delivered:
                        return {"type": "http.request", "body": b"", "more_body": False}
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}

                await self.app(scope, replay_receive, secure_send)
            else:
                await self.app(scope, receive, secure_send)
        finally:
            if acquired:
                self.state.semaphore.release()


def install_security_middleware(app: FastAPI) -> SecurityState:
    settings = SecuritySettings(
        max_body_bytes=_positive_int(
            "REPOGUARD_MAX_BODY_BYTES",
            int(os.environ.get("REPOGUARD_MAX_REQUEST_BYTES", "32768")),
        ),
        max_concurrent_scans=_positive_int("REPOGUARD_MAX_CONCURRENT_SCANS", 4),
        client_requests_per_minute=_positive_int("REPOGUARD_CLIENT_REQUESTS_PER_MINUTE", 30),
        repository_scans_per_hour=_positive_int("REPOGUARD_REPOSITORY_SCANS_PER_HOUR", 10),
    )
    state = SecurityState(settings)
    app.add_middleware(SecurityMiddleware, state=state)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "HEAD", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Payment-Signature"],
        expose_headers=["Payment-Required", "Payment-Response"],
        max_age=600,
    )
    return state
