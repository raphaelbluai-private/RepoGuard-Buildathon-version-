from __future__ import annotations

import os
import threading
import time
from collections import defaultdict


_BLOCKED_LEGACY_PATHS = {
    "/api/scan",
    "/api/auth/request-code",
    "/api/auth/verify-code",
    "/api/demo-trigger",
    "/api/demo-resolve",
    "/api/_internal/rate-stats",
    "/api/_internal/x402-stats",
    "/api/repoguard/verify",
}


class ScanConcurrencyGate:
    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("Scan concurrency limit must be at least 1")
        self.limit = limit
        self._semaphore = threading.BoundedSemaphore(limit)

    def try_acquire(self) -> bool:
        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        self._semaphore.release()


def is_public_preview_only() -> bool:
    return os.getenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def provider_allowed_in_launch(provider_info: dict) -> bool:
    if not is_public_preview_only():
        return True
    return bool(provider_info.get("public_scan"))


def is_legacy_route_blocked(path: str) -> bool:
    return path in _BLOCKED_LEGACY_PATHS


def cors_origins() -> list[str]:
    raw = os.getenv("REPOGUARD_CORS_ORIGINS", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


class RequestRateLimiter:
    """In-process launch-surface limiter.

    This is defense in depth. A trusted-proxy/edge limiter is still required
    for production because direct ASGI client identity may collapse behind a
    reverse proxy.
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        if limit < 1 or window_seconds < 1:
            raise ValueError("Rate limit and window must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._windows: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - self.window_seconds
        with self._lock:
            values = [t for t in self._windows[key] if t > cutoff]
            if len(values) >= self.limit:
                self._windows[key] = values
                return False
            values.append(current)
            self._windows[key] = values
            return True

    def retry_after(self, key: str, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        with self._lock:
            values = self._windows.get(key) or []
            if not values:
                return 1
            remaining = self.window_seconds - (current - min(values))
            return max(1, int(remaining) + 1)


class ProviderCircuitBreaker:
    """Small fail-closed breaker for repeated provider failures."""

    def __init__(self, failure_threshold: int, cooldown_seconds: int) -> None:
        if failure_threshold < 1 or cooldown_seconds < 1:
            raise ValueError("Circuit breaker threshold and cooldown must be positive")
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._failures: dict[str, int] = defaultdict(int)
        self._opened_at: dict[str, float] = {}

    def allow_call(self, provider: str, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        with self._lock:
            opened = self._opened_at.get(provider)
            if opened is None:
                return True
            if current - opened >= self.cooldown_seconds:
                self._opened_at.pop(provider, None)
                self._failures[provider] = 0
                return True
            return False

    def record_failure(self, provider: str, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        with self._lock:
            self._failures[provider] += 1
            if self._failures[provider] >= self.failure_threshold:
                self._opened_at[provider] = current

    def record_success(self, provider: str) -> None:
        with self._lock:
            self._failures[provider] = 0
            self._opened_at.pop(provider, None)

    def retry_after(self, provider: str, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        with self._lock:
            opened = self._opened_at.get(provider)
            if opened is None:
                return 0
            remaining = self.cooldown_seconds - (current - opened)
            return max(1, int(remaining) + 1)
