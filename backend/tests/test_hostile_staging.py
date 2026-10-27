"""Non-live hostile-staging acceptance for RepoGuard's hardened launch surface.

These tests exercise adversarial inputs without submitting a real blockchain payment.
"""
import json

import pytest
from fastapi.testclient import TestClient

import commerce_app_v2
import operational_alerts
import payment_operations as po
import source_adapters


@pytest.mark.parametrize("target", [
    "https://127.0.0.1/acme/repo.git",
    "https://10.0.0.1/acme/repo.git",
    "https://169.254.169.254/latest/meta-data",
    "https://192.168.1.10/acme/repo.git",
    "https://[::1]/acme/repo.git",
])
def test_hostile_private_and_metadata_destinations_are_rejected(monkeypatch, target):
    monkeypatch.setenv("REPOGUARD_ALLOW_SELF_HOSTED_PROVIDERS", "1")
    with pytest.raises(ValueError, match="private or reserved"):
        source_adapters.build_clone_url("gitea", target)


def test_hostile_dns_resolution_to_private_address_is_rejected(monkeypatch):
    monkeypatch.setenv("REPOGUARD_ALLOW_SELF_HOSTED_PROVIDERS", "1")
    monkeypatch.setattr(source_adapters, "_resolve_host_ips", lambda host: {"169.254.169.254"})
    with pytest.raises(ValueError, match="private or reserved"):
        source_adapters.build_clone_url("gitea", "https://git.example.com/acme/repo.git")


def test_hosted_provider_cannot_be_redirected_to_attacker_host():
    with pytest.raises(ValueError, match="does not match provider"):
        source_adapters.build_clone_url("github", "https://attacker.example/acme/repo.git")


def test_git_redirects_are_disabled_and_auth_is_host_scoped(monkeypatch):
    monkeypatch.setenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", "0")
    monkeypatch.setenv("REPOGUARD_GITLAB_TOKEN", "hostile-test-token")
    env = source_adapters._git_env("gitlab", "https://gitlab.com/acme/repo.git")
    config = {
        env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"]
        for i in range(int(env["GIT_CONFIG_COUNT"]))
    }
    assert config["http.followRedirects"] == "false"
    assert "http.https://gitlab.com/.extraHeader" in config
    assert all("attacker.example" not in key for key in config)


def test_public_preview_never_attaches_optional_credentials(monkeypatch):
    monkeypatch.setenv("REPOGUARD_PUBLIC_PREVIEW_ONLY", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "should-never-leave-process")
    env = source_adapters._git_env("github", "https://github.com/acme/repo.git")
    serialized = json.dumps(env)
    assert "should-never-leave-process" not in serialized
    assert not any(".extraHeader" in key for key in env.values() if isinstance(key, str))


def test_oversized_request_is_rejected_before_handler_execution(monkeypatch):
    client = TestClient(commerce_app_v2.app)
    monkeypatch.setattr(commerce_app_v2, "MAX_REQUEST_BYTES", 64)
    response = client.post(
        "/v1/repoguard/scan",
        content=b"x" * 65,
        headers={"content-type": "application/json", "content-length": "65"},
    )
    assert response.status_code == 413
    assert response.json()["error"] == "REQUEST_TOO_LARGE"


def test_concurrent_overload_fails_closed(monkeypatch):
    monkeypatch.setattr(commerce_app_v2.SCAN_CONCURRENCY_GATE, "try_acquire", lambda: False)
    with pytest.raises(commerce_app_v2.HTTPException) as exc:
        commerce_app_v2._run_canonical_scan(
            commerce_app_v2.RepoRequest(repo="owner/repo"), "repo_scan"
        )
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == "SCAN_CAPACITY_EXHAUSTED"


def test_alert_boundary_redacts_nested_secret_material():
    event = operational_alerts.emit_alert(
        "HOSTILE_REDACTION_PROBE",
        severity="error",
        component="security",
        detail={
            "authorization": "Bearer secret-value",
            "nested": {"payment_signature": "signed-proof", "safe": "visible"},
        },
    )
    serialized = json.dumps(event)
    assert "secret-value" not in serialized
    assert "signed-proof" not in serialized
    assert event["detail"]["authorization"] == "[REDACTED]"
    assert event["detail"]["nested"]["payment_signature"] == "[REDACTED]"


def test_payment_proof_replay_is_rejected_without_live_settlement(tmp_path, monkeypatch):
    monkeypatch.setattr(po, "PAYMENT_DB_PATH", str(tmp_path / "hostile-payments.sqlite3"))
    digest = po.payment_proof_digest("hostile-proof")
    first = po.begin_transaction(
        idempotency_key="hostile-a",
        request_hash=po.canonical_request_hash(sku="repo_scan", body={"repo": "owner/repo"}),
        payment_digest=digest,
        sku="repo_scan",
        price_usd="0.07",
        network="eip155:84532",
        facilitator_url="https://x402.org/facilitator",
    )
    with pytest.raises(po.PaymentOperationError) as exc:
        po.begin_transaction(
            idempotency_key="hostile-b",
            request_hash=po.canonical_request_hash(sku="repo_scan", body={"repo": "other/repo"}),
            payment_digest=digest,
            sku="repo_scan",
            price_usd="0.07",
            network="eip155:84532",
            facilitator_url="https://x402.org/facilitator",
        )
    assert exc.value.code == "REPLAY_REJECTED"
    assert exc.value.transaction_id == first.transaction_id
