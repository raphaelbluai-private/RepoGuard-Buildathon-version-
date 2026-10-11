"""RepoGuard x402 payment boundary and discovery declaration.

Protects the paid machine route when explicitly enabled and declares the route
for x402 Bazaar discovery. The scanner itself remains unchanged.
"""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI
from x402.extensions.bazaar import OutputConfig, declare_discovery_extension
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer

BASE_SEPOLIA = "eip155:84532"
BASE_MAINNET = "eip155:8453"
TESTNET_FACILITATOR = "https://x402.org/facilitator"
CDP_FACILITATOR = "https://api.cdp.coinbase.com/platform/v2/x402"
DEFAULT_PRICE = "$0.01"
PROTECTED_ROUTE = "POST /v1/scan"
SERVICE_NAME = "RepoGuard"
SERVICE_TAGS = ["security", "github", "devtools", "repository"]
_EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_FACILITATOR_HOSTS = {"x402.org", "api.cdp.coinbase.com"}

DISCOVERY_EXTENSION = declare_discovery_extension(
    input={"repo": "owner/repository"},
    input_schema={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Public GitHub repository as owner/repo or GitHub URL",
            }
        },
        "required": ["repo"],
        "additionalProperties": False,
    },
    body_type="json",
    output=OutputConfig(
        example={
            "ok": True,
            "service": "repoguard",
            "repo": "owner/repository",
            "commit": "0123456789abcdef",
            "score": 94,
            "status": "SAFE_TO_SHIP",
            "finding_count": 1,
            "cache_hit": False,
        },
        schema={"type": "object"},
    ),
)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def x402_enabled() -> bool:
    return _env_bool("REPOGUARD_X402_ENABLED", False)


def validate_facilitator_url(value: str) -> str:
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.query
        or parsed.port not in (None, 443)
        or hostname not in _FACILITATOR_HOSTS
    ):
        raise RuntimeError("x402 facilitator must be an approved HTTPS endpoint.")
    return value.rstrip("/")


def validate_payment_boundary(
    *, pay_to: str, network: str, facilitator_url: str, allow_mainnet: bool
) -> dict[str, str]:
    if not _EVM_ADDRESS_RE.fullmatch(pay_to):
        raise RuntimeError("x402 pay-to value must be a valid 0x-prefixed EVM address.")
    if network not in {BASE_SEPOLIA, BASE_MAINNET}:
        raise RuntimeError("RepoGuard permits Base Sepolia or Base only.")
    facilitator_url = validate_facilitator_url(facilitator_url)
    if network == BASE_MAINNET:
        if not allow_mainnet:
            raise RuntimeError("Base mainnet is blocked until explicit release authority is recorded.")
        if facilitator_url == TESTNET_FACILITATOR:
            raise RuntimeError("The x402.org facilitator is testnet-only.")
    return {"pay_to": pay_to, "network": network, "facilitator_url": facilitator_url}


def _validate_configuration() -> dict[str, str]:
    pay_to = os.environ.get("REPOGUARD_X402_PAY_TO", "").strip()
    network = os.environ.get("REPOGUARD_X402_NETWORK", BASE_SEPOLIA).strip()
    price = os.environ.get("REPOGUARD_X402_PRICE", DEFAULT_PRICE).strip()
    facilitator_url = os.environ.get(
        "REPOGUARD_X402_FACILITATOR_URL", TESTNET_FACILITATOR
    ).strip()

    boundary = validate_payment_boundary(
        pay_to=pay_to,
        network=network,
        facilitator_url=facilitator_url,
        allow_mainnet=_env_bool("REPOGUARD_X402_ALLOW_MAINNET", False),
    )
    if not re.fullmatch(r"\$\d+(?:\.\d{1,6})?", price):
        raise RuntimeError("REPOGUARD_X402_PRICE must be a dollar price such as $0.01.")
    return {
        "pay_to": boundary["pay_to"],
        "network": boundary["network"],
        "price": price,
        "facilitator_url": boundary["facilitator_url"],
    }


def public_payment_metadata() -> dict[str, Any]:
    """Return non-secret machine-readable payment/discovery metadata."""
    if not x402_enabled():
        return {
            "enabled": False,
            "route": "/v1/scan",
            "method": "POST",
            "protocol": "x402-v2",
            "discovery": "bazaar",
        }
    cfg = _validate_configuration()
    return {
        "enabled": True,
        "route": "/v1/scan",
        "method": "POST",
        "protocol": "x402-v2",
        "scheme": "exact",
        "network": cfg["network"],
        "price": cfg["price"],
        "pay_to": cfg["pay_to"],
        "discovery": "bazaar",
    }


def configure_x402(app: FastAPI) -> dict[str, Any]:
    """Install x402 middleware when explicitly enabled.

    Disabled is a deliberate pre-launch state. Enabled configuration is
    fail-closed: an invalid wallet, unsupported network, insecure facilitator,
    or premature mainnet selection prevents the process from starting.
    """
    if not x402_enabled():
        return {
            "enabled": False,
            "protected": False,
            "route": PROTECTED_ROUTE,
            "network": None,
            "price": None,
            "facilitator": None,
            "bazaar": False,
        }

    cfg = _validate_configuration()
    facilitator = HTTPFacilitatorClient(
        FacilitatorConfig(url=cfg["facilitator_url"])
    )
    server = x402ResourceServer(facilitator)
    server.register(cfg["network"], ExactEvmServerScheme())

    routes: dict[str, RouteConfig] = {
        PROTECTED_ROUTE: RouteConfig(
            accepts=[
                PaymentOption(
                    scheme="exact",
                    pay_to=cfg["pay_to"],
                    price=cfg["price"],
                    network=cfg["network"],
                )
            ],
            mime_type="application/json",
            service_name=SERVICE_NAME,
            tags=SERVICE_TAGS,
            description=(
                "Deterministic Safe-to-Ship analysis for a public GitHub repository. "
                "Returns repository commit, score, deployment status, findings, gates, "
                "and recommended action."
            ),
            extensions=DISCOVERY_EXTENSION,
        )
    }
    app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

    return {
        "enabled": True,
        "protected": True,
        "route": PROTECTED_ROUTE,
        "network": cfg["network"],
        "price": cfg["price"],
        "facilitator": cfg["facilitator_url"],
        "bazaar": True,
    }
