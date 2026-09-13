from __future__ import annotations

import os
import threading


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
