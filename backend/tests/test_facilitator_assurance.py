import pytest

from facilitator_assurance import (
    BASE_MAINNET,
    BASE_SEPOLIA,
    PINNED_X402_VERSION,
    PUBLIC_TESTNET_FACILITATOR,
    can_switch_facilitator,
    classify_facilitator_failure,
    qualification_snapshot,
    validate_facilitator_policy,
)


def test_public_facilitator_is_allowed_for_base_sepolia_but_not_production_qualified():
    snapshot = qualification_snapshot(PUBLIC_TESTNET_FACILITATOR, BASE_SEPOLIA)
    assert snapshot["supported_network"] is True
    assert snapshot["production_qualified"] is False
    assert snapshot["sdk_version"] == PINNED_X402_VERSION


def test_public_testnet_facilitator_is_rejected_for_mainnet():
    with pytest.raises(ValueError, match="not approved"):
        validate_facilitator_policy(PUBLIC_TESTNET_FACILITATOR, BASE_MAINNET)


def test_facilitator_requires_https():
    with pytest.raises(ValueError, match="HTTPS"):
        validate_facilitator_policy("http://facilitator.example", BASE_SEPOLIA)


def test_failover_freezes_after_payment_presentation():
    assert can_switch_facilitator("CHALLENGED") is True
    for state in ("PRESENTED", "VERIFIED", "FULFILLED", "SETTLEMENT_PENDING", "SETTLED"):
        assert can_switch_facilitator(state) is False


def test_settlement_timeout_requires_reconciliation():
    snapshot = qualification_snapshot("https://facilitator.example", BASE_MAINNET)
    assert "reconcile" in snapshot["settlement_timeout_semantics"]
    assert snapshot["automatic_failover_after_payment_presented"] is False


@pytest.mark.parametrize(
    ("phase", "failure", "state", "reconcile", "retryable"),
    [
        ("verify", "timeout", "PRESENTED", False, True),
        ("verify", "5xx", "PRESENTED", False, True),
        ("verify", "malformed response", "VERIFICATION_REJECTED", False, False),
        ("verify", "network unavailable", "PRESENTED", False, True),
        ("settle", "timeout", "SETTLEMENT_PENDING", True, False),
        ("settle", "5xx", "SETTLEMENT_PENDING", True, False),
        ("settle", "malformed response", "SETTLEMENT_PENDING", True, False),
        ("settle", "network unavailable", "SETTLEMENT_PENDING", True, False),
    ],
)
def test_facilitator_failure_matrix(phase, failure, state, reconcile, retryable):
    result = classify_facilitator_failure(phase, failure)
    assert result["state"] == state
    assert result["reconciliation_required"] is reconcile
    assert result["retryable"] is retryable
