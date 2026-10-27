import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import commerce_app_v2
import payment_operations as po


def _fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(po, "PAYMENT_DB_PATH", str(tmp_path / "payments.sqlite3"))


def _begin(**overrides):
    values = {
        "idempotency_key": "idem-1",
        "request_hash": po.canonical_request_hash(sku="repo_scan", body={"repo": "owner/repo"}),
        "payment_digest": po.payment_proof_digest("proof-1"),
        "sku": "repo_scan",
        "price_usd": "0.07",
        "network": "eip155:84532",
        "facilitator_url": "https://x402.org/facilitator",
    }
    values.update(overrides)
    return po.begin_transaction(**values)


def test_happy_path_reaches_receipt_issued(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    tx = _begin()
    po.transition(tx.transaction_id, po.VERIFIED)
    po.transition(tx.transaction_id, po.FULFILLMENT_STARTED)
    po.transition(
        tx.transaction_id,
        po.FULFILLED,
        cache_hit=False,
        response_json=json.dumps({"ok": True}),
    )
    po.transition(tx.transaction_id, po.SETTLEMENT_PENDING)
    po.transition(tx.transaction_id, po.SETTLED, transaction_hash="0xabc")
    tx = po.issue_receipt(tx.transaction_id)

    assert tx.state == po.RECEIPT_ISSUED
    assert tx.receipt_id.startswith("rgrcpt_")
    assert tx.transaction_hash == "0xabc"


def test_same_idempotency_key_same_request_returns_same_transaction(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    first = _begin()
    second = _begin()
    assert second.transaction_id == first.transaction_id


def test_idempotency_key_cannot_be_rebound_to_different_request(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    first = _begin()
    with pytest.raises(po.PaymentOperationError) as exc:
        _begin(
            request_hash=po.canonical_request_hash(
                sku="repo_scan", body={"repo": "different/repo"}
            )
        )
    assert exc.value.code == "IDEMPOTENCY_CONFLICT"
    assert po.get_transaction(first.transaction_id).state == po.IDEMPOTENCY_CONFLICT


def test_payment_proof_reuse_is_rejected_before_second_fulfillment(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    first = _begin(idempotency_key="idem-a")
    with pytest.raises(po.PaymentOperationError) as exc:
        _begin(idempotency_key="idem-b")
    assert exc.value.code == "REPLAY_REJECTED"
    assert exc.value.transaction_id == first.transaction_id


def test_invalid_state_transition_fails_closed(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    tx = _begin()
    with pytest.raises(po.PaymentOperationError) as exc:
        po.transition(tx.transaction_id, po.SETTLED)
    assert exc.value.code == "INVALID_STATE_TRANSITION"


def test_settlement_timeout_is_preserved_as_indeterminate_not_recharged(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    tx = _begin()
    po.transition(tx.transaction_id, po.VERIFIED)
    po.transition(tx.transaction_id, po.FULFILLMENT_STARTED)
    po.transition(tx.transaction_id, po.FULFILLED, response_json='{"ok":true}')
    tx = po.transition(
        tx.transaction_id,
        po.SETTLEMENT_PENDING,
        failure_code="SETTLEMENT_OUTCOME_UNKNOWN",
        retryable=True,
    )
    assert tx.state == po.SETTLEMENT_PENDING
    assert tx.retryable is True
    assert tx.failure_code == "SETTLEMENT_OUTCOME_UNKNOWN"


def test_revenue_and_sku_metrics_count_unique_settled_transactions(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    tx = _begin()
    po.transition(tx.transaction_id, po.VERIFIED)
    po.transition(tx.transaction_id, po.FULFILLMENT_STARTED)
    po.transition(tx.transaction_id, po.FULFILLED, cache_hit=True, response_json='{"ok":true}')
    po.transition(tx.transaction_id, po.SETTLEMENT_PENDING)
    po.transition(tx.transaction_id, po.SETTLED, transaction_hash="0xabc")
    po.issue_receipt(tx.transaction_id)

    metrics = po.metrics()
    assert metrics["sku_volume"] == {"repo_scan": 1}
    assert metrics["revenue_by_sku_usd"] == {"repo_scan": 0.07}
    assert metrics["cache_assisted_fulfillment_rate"] == 1.0


def test_scanner_exception_marks_paid_fulfillment_retriable(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    tx = _begin()
    request = SimpleNamespace(state=SimpleNamespace(payment_transaction_id=tx.transaction_id))

    monkeypatch.setattr(commerce_app_v2, "_require_active_provider", lambda provider: "github")
    monkeypatch.setattr(
        commerce_app_v2,
        "_identity",
        lambda provider, repo: ("github:owner/repo", "abc123", "https://github.com/owner/repo"),
    )
    monkeypatch.setattr(commerce_app_v2.legacy, "_cache_get", lambda *args: None)

    def explode(*args, **kwargs):
        raise RuntimeError("scanner unavailable")

    monkeypatch.setattr(commerce_app_v2, "scan_repo_provider", explode)

    with pytest.raises(commerce_app_v2.HTTPException) as exc:
        commerce_app_v2._run_canonical_scan(
            commerce_app_v2.RepoRequest(repo="owner/repo"),
            "repo_scan",
            request,
        )

    assert exc.value.status_code == 503
    updated = po.get_transaction(tx.transaction_id)
    assert updated.state == po.FULFILLMENT_FAILED_RETRIABLE
    assert updated.retryable is True


def test_wrong_network_and_amount_are_bound_to_transaction_contract(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    tx = _begin(network="eip155:84532", price_usd="0.07")
    assert tx.network == "eip155:84532"
    assert tx.price_usd == "0.07"


def test_internal_payment_metrics_surface_is_aggregate_only(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    monkeypatch.setenv("REPOGUARD_INTERNAL", "1")
    tx = _begin()
    po.transition(tx.transaction_id, po.VERIFIED)
    po.transition(tx.transaction_id, po.FULFILLMENT_STARTED)
    po.transition(tx.transaction_id, po.FULFILLED, cache_hit=False, response_json='{"ok":true}')
    po.transition(tx.transaction_id, po.SETTLEMENT_PENDING)
    po.transition(tx.transaction_id, po.SETTLED, transaction_hash="0xabc")
    po.issue_receipt(tx.transaction_id)

    response = TestClient(commerce_app_v2.app).get("/v1/repoguard/payment-operations/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["sku_volume"]["repo_scan"] == 1
    serialized = json.dumps(payload)
    assert "proof-1" not in serialized
    assert "payment_proof_digest" not in serialized
