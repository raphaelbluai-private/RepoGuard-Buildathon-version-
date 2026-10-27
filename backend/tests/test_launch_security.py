import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import commerce_app_v2
from launch_security import (
    ProviderCircuitBreaker,
    RequestRateLimiter,
    ScanConcurrencyGate,
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


def test_hardened_commerce_surface_emits_baseline_security_headers():
    client = TestClient(commerce_app_v2.app)
    response = client.get("/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["strict-transport-security"].startswith("max-age=")
    assert response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    assert response.headers["cache-control"] == "no-store"


def test_scan_concurrency_gate_fails_closed_when_capacity_is_exhausted():
    gate = ScanConcurrencyGate(limit=1)
    assert gate.try_acquire() is True
    assert gate.try_acquire() is False
    gate.release()
    assert gate.try_acquire() is True
    gate.release()


def test_commerce_scan_rejects_when_concurrency_capacity_is_exhausted(monkeypatch):
    monkeypatch.setattr(commerce_app_v2.SCAN_CONCURRENCY_GATE, "try_acquire", lambda: False)
    body = commerce_app_v2.RepoRequest(repo="owner/repo", provider="github")
    with pytest.raises(HTTPException) as exc:
        commerce_app_v2._run_canonical_scan(body, "repo_scan")
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == "SCAN_CAPACITY_EXHAUSTED"



def test_request_rate_limiter_uses_bounded_window():
    limiter = RequestRateLimiter(limit=2, window_seconds=10)
    assert limiter.allow("client", now=100.0) is True
    assert limiter.allow("client", now=101.0) is True
    assert limiter.allow("client", now=102.0) is False
    assert limiter.retry_after("client", now=102.0) >= 1
    assert limiter.allow("client", now=111.1) is True


def test_hardened_commerce_post_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr(
        commerce_app_v2,
        "REQUEST_RATE_LIMITER",
        RequestRateLimiter(limit=1, window_seconds=60),
    )
    client = TestClient(commerce_app_v2.app)
    body = {"repo": "owner/repo", "provider": "unsupported"}
    first = client.post("/v1/repoguard/preflight", json=body)
    second = client.post("/v1/repoguard/preflight", json=body)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"] == "RATE_LIMITED"
    assert int(second.headers["retry-after"]) >= 1


def test_provider_circuit_breaker_opens_and_recovers():
    breaker = ProviderCircuitBreaker(failure_threshold=2, cooldown_seconds=30)
    assert breaker.allow_call("github", now=100.0) is True
    breaker.record_failure("github", now=101.0)
    assert breaker.allow_call("github", now=102.0) is True
    breaker.record_failure("github", now=103.0)
    assert breaker.allow_call("github", now=104.0) is False
    assert breaker.retry_after("github", now=104.0) >= 1
    assert breaker.allow_call("github", now=134.0) is True


def test_provider_circuit_opens_after_repeated_runtime_failures(monkeypatch):
    breaker = ProviderCircuitBreaker(failure_threshold=2, cooldown_seconds=30)
    monkeypatch.setattr(commerce_app_v2, "PROVIDER_CIRCUIT_BREAKER", breaker)
    monkeypatch.setattr(
        commerce_app_v2,
        "repo_head_identity",
        lambda provider, repo: (_ for _ in ()).throw(TimeoutError("provider timeout")),
    )

    for _ in range(2):
        with pytest.raises(HTTPException):
            commerce_app_v2._identity("github", "owner/repo")

    with pytest.raises(HTTPException) as exc:
        commerce_app_v2._identity("github", "owner/repo")
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == "PROVIDER_CIRCUIT_OPEN"
    assert int(exc.value.headers["Retry-After"]) >= 1
