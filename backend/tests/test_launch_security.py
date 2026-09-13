from fastapi.testclient import TestClient

import commerce_app_v2
from launch_security import (
    cors_origins,
    is_legacy_route_blocked,
    is_public_preview_only,
    provider_allowed_in_launch,
)


def test_public_preview_only_is_secure_default(monkeypatch):
    monkeypatch.delenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", raising=False)
    assert is_public_preview_only() is True


def test_public_preview_can_be_explicitly_disabled(monkeypatch):
    monkeypatch.setenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", "0")
    assert is_public_preview_only() is False


def test_public_preview_allows_only_public_scan_providers(monkeypatch):
    monkeypatch.delenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", raising=False)
    assert provider_allowed_in_launch({"public_scan": True}) is True
    assert provider_allowed_in_launch({"public_scan": False, "auth_required": True}) is False


def test_private_provider_can_be_enabled_after_preview(monkeypatch):
    monkeypatch.setenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", "0")
    assert provider_allowed_in_launch({"public_scan": False, "auth_required": True}) is True


def test_legacy_commercial_bypass_and_demo_routes_are_blocked():
    blocked = [
        "/api/scan",
        "/api/auth/request-code",
        "/api/auth/verify-code",
        "/api/demo-trigger",
        "/api/demo-resolve",
        "/api/_internal/rate-stats",
        "/api/_internal/x402-stats",
        "/api/repoguard/verify",
    ]
    assert all(is_legacy_route_blocked(path) for path in blocked)
    assert is_legacy_route_blocked("/api/health") is False
    assert is_legacy_route_blocked("/") is False


def test_cors_is_closed_by_default(monkeypatch):
    monkeypatch.delenv("REPOGUARD_CORS_ORIGINS", raising=False)
    assert cors_origins() == []


def test_cors_parses_explicit_origins(monkeypatch):
    monkeypatch.setenv(
        "REPOGUARD_CORS_ORIGINS",
        "https://repoguard.example, https://app.example",
    )
    assert cors_origins() == ["https://repoguard.example", "https://app.example"]


def test_hardened_commerce_surface_does_not_emit_wildcard_cors():
    client = TestClient(commerce_app_v2.app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "*"
