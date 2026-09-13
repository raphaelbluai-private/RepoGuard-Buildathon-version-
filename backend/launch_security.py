from __future__ import annotations

import os


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
