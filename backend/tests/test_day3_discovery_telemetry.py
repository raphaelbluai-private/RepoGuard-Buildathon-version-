import os

from fastapi.testclient import TestClient

os.environ.setdefault("REPOGUARD_INTERNAL", "1")
os.environ.setdefault("REPOGUARD_CACHE_DB", "/tmp/repoguard-test-cache.sqlite3")
os.environ.setdefault("REPOGUARD_TELEMETRY_DB", "/tmp/repoguard-test-commerce.sqlite3")

import commerce_telemetry
import commercial_app
import x402_payments


def test_bazaar_extension_declares_repo_body():
    bazaar = x402_payments.DISCOVERY_EXTENSION["bazaar"]
    assert bazaar["info"]["input"]["type"] == "http"
    assert bazaar["info"]["input"]["bodyType"] == "json"
    schema = bazaar["schema"]["properties"]["input"]["properties"]["body"]
    assert "repo" in schema["properties"]
    assert "repo" in schema["required"]


def test_well_known_manifest_is_machine_readable():
    client = TestClient(commercial_app.app)
    response = client.get("/.well-known/x402")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "RepoGuard"
    assert body["payment"]["route"] == "/v1/scan"
    assert body["payment"]["protocol"] == "x402-v2"
    assert body["input"]["schema"]["required"] == ["repo"]


def test_telemetry_summary_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        commerce_telemetry, "TELEMETRY_DB_PATH", str(tmp_path / "commerce.sqlite3")
    )
    commerce_telemetry.record_event("payment_challenge", status_code=402)
    commerce_telemetry.record_scan_served(cache_hit=False)
    commerce_telemetry.record_scan_served(cache_hit=True)
    commerce_telemetry.record_x402_response(
        200,
        {
            "PAYMENT-RESPONSE": '{"success":true,"network":"eip155:84532","transaction":"0xabc","payer":"0xdef"}'
        },
    )
    summary = commerce_telemetry.summary()
    assert summary["payment_challenges"] == 1
    assert summary["payments_settled"] == 1
    assert summary["scans_served"] == 2
    assert summary["cache_hits"] == 1
