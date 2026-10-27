from pathlib import Path

import operational_readiness as readiness


def test_operational_readiness_reports_green_engineering_paths(tmp_path, monkeypatch):
    for key, name in (
        ("REPOGUARD_CACHE_DB", "cache.sqlite3"),
        ("REPOGUARD_TELEMETRY_DB", "telemetry.sqlite3"),
        ("REPOGUARD_PAYMENT_DB", "payments.sqlite3"),
    ):
        monkeypatch.setenv(key, str(tmp_path / name))
    monkeypatch.setenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "1")
    monkeypatch.setenv("REPOGUARD_RELEASE_SHA", "a" * 40)
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deployment-test")

    result = readiness.operational_readiness()
    assert result["status"] == "ENGINEERING_READY"
    assert result["release_authorized"] is False
    assert result["blockers"] == []
    assert all(item["parent_writable"] for item in result["persistence"])
    assert "base_sepolia_acceptance" in result["live_evidence_required"]


def test_operational_readiness_fails_closed_on_missing_persistence(monkeypatch, tmp_path):
    monkeypatch.setenv("REPOGUARD_CACHE_DB", "relative-cache.sqlite3")
    monkeypatch.delenv("REPOGUARD_TELEMETRY_DB", raising=False)
    monkeypatch.setenv("REPOGUARD_PAYMENT_DB", str(tmp_path / "payments.sqlite3"))
    monkeypatch.setenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "0")

    result = readiness.operational_readiness()
    assert result["status"] == "BLOCKED"
    assert "persistent_state_not_ready" in result["blockers"]


def test_operational_readiness_fails_closed_when_identity_required_but_unknown(tmp_path, monkeypatch):
    for key, name in (
        ("REPOGUARD_CACHE_DB", "cache.sqlite3"),
        ("REPOGUARD_TELEMETRY_DB", "telemetry.sqlite3"),
        ("REPOGUARD_PAYMENT_DB", "payments.sqlite3"),
    ):
        monkeypatch.setenv(key, str(tmp_path / name))
    monkeypatch.setenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "1")
    for key in ("REPOGUARD_RELEASE_SHA", "RAILWAY_GIT_COMMIT_SHA", "GITHUB_SHA",
                "RAILWAY_DEPLOYMENT_ID", "REPOGUARD_DEPLOYMENT_ID", "REPOGUARD_IMAGE_DIGEST"):
        monkeypatch.delenv(key, raising=False)

    result = readiness.operational_readiness()
    assert result["status"] == "BLOCKED"
    assert "runtime_identity_incomplete" in result["blockers"]
