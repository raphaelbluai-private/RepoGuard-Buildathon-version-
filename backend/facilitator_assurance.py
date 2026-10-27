"""Facilitator qualification and failover policy for RepoGuard payment operations."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

BASE_SEPOLIA = "eip155:84532"
BASE_MAINNET = "eip155:8453"
PUBLIC_TESTNET_FACILITATOR = "https://x402.org/facilitator"
PINNED_X402_VERSION = "2.22.0"


@dataclass(frozen=True)
class FacilitatorPolicy:
    url: str
    network: str
    production_qualified: bool
    automatic_failover_before_payment: bool
    automatic_failover_after_payment_presented: bool
    settlement_timeout_is_indeterminate: bool
    pinned_sdk_version: str


def validate_facilitator_policy(url: str, network: str) -> FacilitatorPolicy:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Facilitator URL must be an absolute HTTPS URL.")
    if network not in {BASE_SEPOLIA, BASE_MAINNET}:
        raise ValueError("RepoGuard permits only Base Sepolia or Base for the approved x402 rail.")

    public_testnet = url.rstrip("/") == PUBLIC_TESTNET_FACILITATOR
    if network == BASE_MAINNET and public_testnet:
        raise ValueError("The public x402.org facilitator is not approved for RepoGuard mainnet.")

    return FacilitatorPolicy(
        url=url.rstrip("/"),
        network=network,
        production_qualified=(network == BASE_MAINNET and not public_testnet),
        automatic_failover_before_payment=True,
        automatic_failover_after_payment_presented=False,
        settlement_timeout_is_indeterminate=True,
        pinned_sdk_version=PINNED_X402_VERSION,
    )


def can_switch_facilitator(transaction_state: str) -> bool:
    """Failover is allowed only before a payment authorization is presented."""
    return transaction_state == "CHALLENGED"


def qualification_snapshot(url: str, network: str) -> dict:
    policy = validate_facilitator_policy(url, network)
    return {
        "url": policy.url,
        "network": policy.network,
        "sdk_version": policy.pinned_sdk_version,
        "supported_network": True,
        "settlement_semantics": "authorization: verify -> fulfill -> settle -> respond",
        "settlement_timeout_semantics": "indeterminate; reconcile before retrying payment",
        "automatic_failover_before_payment": policy.automatic_failover_before_payment,
        "automatic_failover_after_payment_presented": policy.automatic_failover_after_payment_presented,
        "production_qualified": policy.production_qualified,
        "evidence_required": {
            "measured_reliability": True,
            "rate_volume_limits": True,
            "failure_behavior": True,
            "incident_failover_runbook": True,
        },
    }
