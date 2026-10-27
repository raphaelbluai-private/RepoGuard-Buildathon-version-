import json
import os
import subprocess
import sys

import pytest

import operational_alerts
import performance_budgets
import runtime_identity


def _run_backend(code: str, env: dict[str, str]) -> str:
    process_env = os.environ.copy()
    process_env.update(env)
    process_env["PYTHONPATH"] = os.getcwd()
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env=process_env,
    )
    return result.stdout.strip()


def test_paid_state_survives_process_restart(tmp_path):
    cache_db = tmp_path / "cache.sqlite3"
    payment_db = tmp_path / "payments.sqlite3"
    telemetry_db = tmp_path / "telemetry.sqlite3"
    env = {
        "REPOGUARD_CACHE_DB": str(cache_db),
        "REPOGUARD_PAYMENT_DB": str(payment_db),
        "REPOGUARD_TELEMETRY_DB": str(telemetry_db),
    }

    _run_backend(
        """
from persistent_scan_cache import put
from payment_operations import begin_transaction, canonical_request_hash, payment_proof_digest
from commerce_telemetry import record_event
put("github:owner/repo", "abc123", {"ok": True, "value": 7})
begin_transaction(
    idempotency_key="restart-idem",
    request_hash=canonical_request_hash(sku="repo_scan", body={"repo":"owner/repo"}),
    payment_digest=payment_proof_digest("restart-proof"),
    sku="repo_scan",
    price_usd="0.07",
    network="eip155:84532",
    facilitator_url="https://x402.org/facilitator",
)
record_event("restart_probe", status_code=200)
""",
        env,
    )

    output = _run_backend(
        """
import json
import os
from persistent_scan_cache import get
from payment_operations import get_by_idempotency
import sqlite3
tx = get_by_idempotency("restart-idem")
with sqlite3.connect(os.environ["REPOGUARD_TELEMETRY_DB"]) as conn:
    telemetry_count = conn.execute(
        "SELECT COUNT(*) FROM commerce_events WHERE event_type='restart_probe'"
    ).fetchone()[0]
print(json.dumps({
    "cache": get("github:owner/repo", "abc123"),
    "transaction_state": tx.state if tx else None,
    "telemetry_count": telemetry_count,
}))
""",
        env,
    )
    data = json.loads(output)
    assert data["cache"] == {"ok": True, "value": 7}
    assert data["transaction_state"] == "PRESENTED"
    assert cache_db.exists()
    assert payment_db.exists()
    assert telemetry_db.exists()
    assert data["telemetry_count"] == 1


def test_runtime_identity_hash_uses_safe_configuration_only(monkeypatch):
    monkeypatch.setenv("REPOGUARD_X402_NETWORK", "eip155:84532")
    monkeypatch.setenv("REPOGUARD_PAY_TO", "0xDO_NOT_HASH_ME")
    safe = runtime_identity.safe_configuration()
    assert "REPOGUARD_PAY_TO" not in safe
    assert runtime_identity.configuration_hash().startswith("sha256:")


def test_runtime_identity_fails_closed_when_required(monkeypatch):
    monkeypatch.setenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "1")
    for key in (
        "REPOGUARD_RELEASE_SHA",
        "RAILWAY_GIT_COMMIT_SHA",
        "GITHUB_SHA",
        "RAILWAY_DEPLOYMENT_ID",
        "REPOGUARD_DEPLOYMENT_ID",
        "REPOGUARD_IMAGE_DIGEST",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="Runtime identity is required"):
        runtime_identity.require_runtime_identity()


def test_runtime_identity_accepts_source_and_deployment(monkeypatch):
    monkeypatch.setenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "1")
    monkeypatch.setenv("REPOGUARD_RELEASE_SHA", "a" * 40)
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deployment-1")
    runtime_identity.require_runtime_identity()
    view = runtime_identity.runtime_identity_view()
    assert view["source_commit"] == "a" * 40
    assert view["deployment_id"] == "deployment-1"
    assert view["identity_complete"] is True


def test_structured_alert_contract(caplog):
    event = operational_alerts.emit_alert(
        "SCAN_CAPACITY_EXHAUSTED",
        severity="warning",
        component="scanner",
        transaction_id="rgtx_example",
        retryable=True,
        detail={"safe": "value"},
    )
    assert event["event"] == "repoguard_operational_alert"
    assert event["severity"] == "WARNING"
    assert event["alert_id"].startswith("rga_")
    assert event["transaction_id"] == "rgtx_example"


def test_performance_budget_evaluator_pass_and_fail():
    passing = performance_budgets.evaluate("verify", [100, 200, 300, 400, 500])
    failing = performance_budgets.evaluate("verify", [1000, 2000, 4000, 5000, 6000])
    assert passing["passes"] is True
    assert failing["passes"] is False


def test_runtime_identity_rejects_authorized_release_drift(monkeypatch):
    monkeypatch.setenv("REPOGUARD_RELEASE_SHA", "a" * 40)
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deployment-1")
    monkeypatch.setenv("REPOGUARD_AUTHORIZED_RELEASE_SHA", "b" * 40)
    with pytest.raises(RuntimeError, match="does not match authorized release"):
        runtime_identity.require_runtime_identity()
