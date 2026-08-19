import json
import os
import subprocess
import sys

import pytest

import x402_payments


TEST_WALLET = "0x000000000000000000000000000000000000dEaD"


def test_x402_disabled_by_default(monkeypatch):
    monkeypatch.delenv("REPOGUARD_X402_ENABLED", raising=False)
    assert x402_payments.x402_enabled() is False


def test_x402_enabled_requires_valid_wallet(monkeypatch):
    monkeypatch.setenv("REPOGUARD_X402_ENABLED", "1")
    monkeypatch.setenv("REPOGUARD_X402_PAY_TO", "not-a-wallet")
    with pytest.raises(RuntimeError, match="valid 0x-prefixed EVM address"):
        x402_payments._validate_configuration()


def test_mainnet_is_blocked_without_explicit_release_authority(monkeypatch):
    monkeypatch.setenv("REPOGUARD_X402_PAY_TO", TEST_WALLET)
    monkeypatch.setenv("REPOGUARD_X402_NETWORK", x402_payments.BASE_MAINNET)
    monkeypatch.delenv("REPOGUARD_X402_ALLOW_MAINNET", raising=False)
    with pytest.raises(RuntimeError, match="Base mainnet is blocked"):
        x402_payments._validate_configuration()


def test_testnet_configuration_is_base_sepolia(monkeypatch):
    monkeypatch.setenv("REPOGUARD_X402_PAY_TO", TEST_WALLET)
    monkeypatch.delenv("REPOGUARD_X402_NETWORK", raising=False)
    monkeypatch.delenv("REPOGUARD_X402_PRICE", raising=False)
    monkeypatch.delenv("REPOGUARD_X402_FACILITATOR_URL", raising=False)
    cfg = x402_payments._validate_configuration()
    assert cfg["network"] == "eip155:84532"
    assert cfg["price"] == "$0.01"
    assert cfg["facilitator_url"] == "https://x402.org/facilitator"


def _run_enabled_probe(extra_headers=None):
    headers = extra_headers or {}
    script = f'''
import json
import os
os.environ["REPOGUARD_X402_ENABLED"] = "1"
os.environ["REPOGUARD_X402_PAY_TO"] = "{TEST_WALLET}"
os.environ["REPOGUARD_X402_NETWORK"] = "eip155:84532"
os.environ["REPOGUARD_X402_PRICE"] = "$0.01"
os.environ["REPOGUARD_X402_FACILITATOR_URL"] = "https://x402.org/facilitator"
os.environ["REPOGUARD_INTERNAL"] = "1"
from fastapi.testclient import TestClient
import commercial_app
client = TestClient(commercial_app.app)
response = client.post("/v1/scan", json={{"repo": "acme/service"}}, headers={headers!r})
print(json.dumps({{
    "status": response.status_code,
    "payment_required": "payment-required" in {{k.lower() for k in response.headers.keys()}},
    "payment_response": response.headers.get("PAYMENT-RESPONSE"),
}}))
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    proc = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_no_payment_returns_402_with_payment_required_header():
    result = _run_enabled_probe()
    assert result["status"] == 402
    assert result["payment_required"] is True


def test_invalid_payment_signature_is_denied():
    result = _run_enabled_probe({"PAYMENT-SIGNATURE": "invalid-payment-payload"})
    assert result["status"] != 200
