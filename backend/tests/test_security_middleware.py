from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from security_middleware import install_security_middleware


def build_client(monkeypatch, **settings):
    defaults = {
        "REPOGUARD_ALLOWED_ORIGINS": "https://app.example.com",
        "REPOGUARD_MAX_BODY_BYTES": "64",
        "REPOGUARD_MAX_CONCURRENT_SCANS": "1",
        "REPOGUARD_CLIENT_REQUESTS_PER_MINUTE": "2",
        "REPOGUARD_REPOSITORY_SCANS_PER_HOUR": "1",
    }
    defaults.update({key: str(value) for key, value in settings.items()})
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)
    app = FastAPI()

    @app.post("/v1/repoguard/scan")
    def scan(body: dict):
        return body

    state = install_security_middleware(app)
    client = TestClient(app)
    client.security_state = state
    return client


def test_cors_allows_only_configured_origin(monkeypatch):
    client = build_client(monkeypatch)
    allowed = client.options(
        "/v1/repoguard/scan",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    denied = client.options(
        "/v1/repoguard/scan",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://app.example.com"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.parametrize("origin", ["*", "http://app.example.com", "https://app.example.com/path"])
def test_unsafe_cors_configuration_fails_startup(monkeypatch, origin):
    monkeypatch.setenv("REPOGUARD_ALLOWED_ORIGINS", origin)
    with pytest.raises(RuntimeError):
        install_security_middleware(FastAPI())


def test_oversized_request_is_rejected(monkeypatch):
    client = build_client(monkeypatch)
    response = client.post("/v1/repoguard/scan", json={"repo": "x" * 100})
    assert response.status_code == 413


def test_repository_quota_and_forwarded_header_resistance(monkeypatch):
    client = build_client(monkeypatch, REPOGUARD_CLIENT_REQUESTS_PER_MINUTE=10)
    assert client.post("/v1/repoguard/scan", json={"repo": "acme/service"}).status_code == 200
    response = client.post(
        "/v1/repoguard/scan",
        json={"repo": "acme/service"},
        headers={"X-Forwarded-For": "203.0.113.1"},
    )
    assert response.status_code == 429
    assert response.json()["error"] == "REPOSITORY_QUOTA_EXCEEDED"


def test_client_quota_and_security_headers(monkeypatch):
    client = build_client(
        monkeypatch,
        REPOGUARD_CLIENT_REQUESTS_PER_MINUTE=1,
        REPOGUARD_REPOSITORY_SCANS_PER_HOUR=10,
    )
    first = client.post("/v1/repoguard/scan", json={"repo": "acme/one"})
    second = client.post("/v1/repoguard/scan", json={"repo": "acme/two"})
    assert first.headers["x-content-type-options"] == "nosniff"
    assert first.headers["x-frame-options"] == "DENY"
    assert first.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in first.headers["content-security-policy"]
    assert second.status_code == 429
    assert second.json()["error"] == "CLIENT_RATE_LIMIT_EXCEEDED"


def test_concurrency_exhaustion_fails_closed(monkeypatch):
    client = build_client(monkeypatch)
    assert client.security_state.semaphore.acquire(blocking=False)
    try:
        response = client.post("/v1/repoguard/scan", json={"repo": "acme/service"})
    finally:
        client.security_state.semaphore.release()
    assert response.status_code == 503
    assert response.json()["error"] == "SCAN_CAPACITY_EXHAUSTED"
