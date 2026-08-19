import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

os.environ["REPOGUARD_INTERNAL"] = "1"
os.environ["REPOGUARD_CACHE_DB"] = "/tmp/repoguard-test-cache.sqlite3"

import commercial
import commercial_app


@pytest.fixture(autouse=True)
def isolate_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(commercial, "CACHE_DB_PATH", str(tmp_path / "cache.sqlite3"))
    commercial_app.limiter._windows.clear()
    commercial_app.limiter._lockouts.clear()
    commercial_app.limiter._failed_auth.clear()


@pytest.fixture
def client():
    return TestClient(commercial_app.app)


def _identity():
    return {
        "ok": True,
        "owner": "acme",
        "repo": "service",
        "full_name": "acme/service",
        "default_branch": "main",
        "commit_sha": "abc123",
    }


def _scan(status="SAFE_TO_SHIP", score=100, findings=None):
    return {
        "ok": True,
        "rulesExecuted": 12,
        "score": score,
        "status": status,
        "findings": findings or [],
        "gates": [],
    }


def test_health_contract(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "repoguard"
    assert body["version"] == "1.0"
    assert "github_authenticated" in body


def test_v1_scan_contract(client, monkeypatch):
    monkeypatch.setattr(commercial, "resolve_repo_identity", lambda _: _identity())
    monkeypatch.setattr(commercial, "scan_repo", lambda _: _scan())
    response = client.post("/v1/scan", json={"repo": "acme/service"})
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "repoguard"
    assert body["repo"] == "acme/service"
    assert body["commit"] == "abc123"
    assert body["status"] == "SAFE_TO_SHIP"
    assert body["rules_executed"] == 12
    assert body["finding_count"] == 0
    assert body["recommended_action"] == "PROCEED_TO_DEPLOYMENT"
    assert body["cache_hit"] is False


def test_v1_second_same_sha_is_cache_hit(client, monkeypatch):
    monkeypatch.setattr(commercial, "resolve_repo_identity", lambda _: _identity())
    calls = {"count": 0}

    def fake_scan(_):
        calls["count"] += 1
        return _scan()

    monkeypatch.setattr(commercial, "scan_repo", fake_scan)
    first = client.post("/v1/scan", json={"repo": "acme/service"})
    second = client.post("/v1/scan", json={"repo": "acme/service"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] == 1
    assert second.json()["cache_hit"] is True


def test_new_sha_forces_rescan(client, monkeypatch):
    state = {"sha": "abc123"}

    def identity(_):
        value = _identity()
        value["commit_sha"] = state["sha"]
        return value

    calls = {"count": 0}
    monkeypatch.setattr(commercial, "resolve_repo_identity", identity)
    monkeypatch.setattr(
        commercial,
        "scan_repo",
        lambda _: calls.__setitem__("count", calls["count"] + 1) or _scan(),
    )
    client.post("/v1/scan", json={"repo": "acme/service"})
    state["sha"] = "def456"
    client.post("/v1/scan", json={"repo": "acme/service"})
    assert calls["count"] == 2


def test_invalid_repo_returns_400(client, monkeypatch):
    monkeypatch.setattr(
        commercial,
        "resolve_repo_identity",
        lambda _: {"ok": False, "error": "INVALID_INPUT", "message": "bad"},
    )
    response = client.post("/v1/scan", json={"repo": "bad"})
    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_INPUT"


def test_upstream_failure_returns_502(client, monkeypatch):
    monkeypatch.setattr(
        commercial,
        "resolve_repo_identity",
        lambda _: {"ok": False, "error": "GITHUB_ERROR", "message": "upstream"},
    )
    response = client.post("/v1/scan", json={"repo": "acme/service"})
    assert response.status_code == 502


def test_findings_are_counted_by_severity():
    findings = [
        {"severity": "critical"},
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "low"},
        {"severity": "low"},
    ]
    payload = commercial.to_v1_contract(
        _scan(status="SHIP_BLOCKED", score=49, findings=findings),
        _identity(),
        cache_hit=False,
    )
    assert payload["finding_count"] == 5
    assert payload["critical"] == 1
    assert payload["high"] == 1
    assert payload["medium"] == 1
    assert payload["low"] == 2
    assert payload["recommended_action"] == "REMEDIATE_BEFORE_DEPLOYMENT"


def test_needs_review_recommendation():
    payload = commercial.to_v1_contract(
        _scan(status="NEEDS_REVIEW", score=80), _identity(), cache_hit=False
    )
    assert payload["recommended_action"] == "REVIEW_FINDINGS_BEFORE_DEPLOYMENT"


def test_cache_key_includes_sha_and_scanner_version(monkeypatch):
    monkeypatch.setattr(commercial, "SCANNER_VERSION", "1.9")
    key = commercial.cache_key("Acme", "Service", "main", "abc123")
    assert key == "acme:service:main:abc123:1.9"


def test_cache_round_trip(monkeypatch, tmp_path):
    monkeypatch.setattr(commercial, "CACHE_DB_PATH", str(tmp_path / "cache.sqlite3"))
    payload = {"ok": True, "status": "SAFE_TO_SHIP"}
    commercial.cache_put("k", "acme", "service", "main", "abc", payload)
    assert commercial.cache_get("k") == payload


def test_cache_expiry(monkeypatch, tmp_path):
    monkeypatch.setattr(commercial, "CACHE_DB_PATH", str(tmp_path / "cache.sqlite3"))
    monkeypatch.setattr(commercial, "CACHE_TTL_SECONDS", -1)
    commercial.cache_put("k", "acme", "service", "main", "abc", {"ok": True})
    assert commercial.cache_get("k") is None


def test_github_auth_header_uses_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token-123")
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert commercial._github_headers()["Authorization"] == "Bearer token-123"


def test_github_auth_header_absent_without_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert "Authorization" not in commercial._github_headers()


def test_rate_limit_eventually_returns_429(client, monkeypatch):
    monkeypatch.setattr(commercial, "resolve_repo_identity", lambda _: _identity())
    monkeypatch.setattr(commercial, "scan_repo", lambda _: _scan())
    statuses = [
        client.post("/v1/scan", json={"repo": "acme/service"}).status_code
        for _ in range(31)
    ]
    assert statuses[:30] == [200] * 30
    assert statuses[30] == 429


def test_missing_repo_body_is_validation_error(client):
    response = client.post("/v1/scan", json={})
    assert response.status_code == 422
