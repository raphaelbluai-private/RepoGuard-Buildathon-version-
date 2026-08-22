from __future__ import annotations

import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import app as legacy
from commerce_contracts import provider_capabilities, remediation_view, safe_to_ship_view
from commerce_telemetry import record_event
from product_catalog import PRODUCTS, discovery_catalog, get_product
from provenance import build_attestation, build_provenance
from scanner import scan_repo

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer


app = FastAPI(title="RepoGuard Agent Commerce API", version="2.0.0")

X402_NETWORK = os.environ.get("REPOGUARD_X402_NETWORK", getattr(legacy, "X402_NETWORK", "eip155:84532"))
X402_PAY_TO = os.environ.get("REPOGUARD_PAY_TO")
X402_FACILITATOR_URL = os.environ.get("REPOGUARD_X402_FACILITATOR_URL", "https://x402.org/facilitator")


@app.get("/v1/health", include_in_schema=False)
def v1_health():
    """Railway compatibility healthcheck for legacy deployment metadata."""
    return {
        "status": "ok",
        "service": "RepoGuard",
        "api_version": "2.0.0",
    }


class RepoRequest(BaseModel):
    repo: str
    provider: str = "github"


class VerifyCommitRequest(RepoRequest):
    expected_commit_sha: str


def _provider_key(provider: str) -> str:
    return (provider or "github").strip().lower().replace("-", "_").replace(" ", "_")


def _require_active_provider(provider: str) -> str:
    key = _provider_key(provider)
    capabilities = provider_capabilities()
    if key not in capabilities:
        raise HTTPException(
            status_code=422,
            detail={"error": "UNSUPPORTED_PROVIDER", "provider": key, "providers": capabilities},
        )
    if capabilities[key].get("status") != "active":
        raise HTTPException(
            status_code=501,
            detail={
                "error": "PROVIDER_ADAPTER_NOT_ACTIVE",
                "provider": key,
                "status": capabilities[key].get("status"),
                "message": "RepoGuard preserves this provider in the source-provider contract, but its production adapter is not active yet.",
            },
        )
    return key


def _run_canonical_scan(body: RepoRequest, sku: str) -> dict[str, Any]:
    provider = _require_active_provider(body.provider)
    if provider != "github":
        raise HTTPException(status_code=501, detail={"error": "PROVIDER_ADAPTER_NOT_ACTIVE", "provider": provider})

    started = time.monotonic()
    repo_key, head_sha = legacy._repo_head_identity(body.repo)
    cached = legacy._cache_get(repo_key, head_sha)
    cache_hit = cached is not None

    if cache_hit:
        result = cached
    else:
        try:
            result = scan_repo(body.repo)
        except Exception as exc:
            result = {
                "ok": False,
                "error": "SCAN_ERROR",
                "message": f"Scan failed unexpectedly: {type(exc).__name__}",
            }
        legacy._cache_put(repo_key, head_sha, result)

    if not isinstance(result, dict):
        result = {"ok": False, "error": "INVALID_SCAN_RESULT"}

    repository = repo_key or body.repo
    repository_url = (
        (result.get("repo") or {}).get("url")
        if isinstance(result.get("repo"), dict)
        else None
    ) or f"https://github.com/{repository}"

    provenance = build_provenance(
        provider=provider,
        repository=repository,
        repository_url=repository_url,
        commit_sha=head_sha,
        result=result,
    )

    latency_ms = round((time.monotonic() - started) * 1000, 2)
    record_event(
        "product_fulfilled",
        status_code=200,
        network=X402_NETWORK,
        cache_hit=cache_hit,
        detail={
            "sku": sku,
            "repository": repository,
            "scan_id": provenance["scan_id"],
            "latency_ms": latency_ms,
        },
    )

    return {
        "provider": provider,
        "repository": repository,
        "head_sha": head_sha,
        "cache_hit": cache_hit,
        "latency_ms": latency_ms,
        "result": result,
        "provenance": provenance,
    }


@app.get("/v1/repoguard/products")
def products():
    return {
        "service": "RepoGuard",
        "positioning": "Deterministic pre-deployment assurance for agents and software pipelines.",
        "network": X402_NETWORK,
        "products": discovery_catalog(),
        "providers": provider_capabilities(),
    }


@app.post("/v1/repoguard/preflight")
def preflight(body: RepoRequest):
    provider = _provider_key(body.provider)
    capabilities = provider_capabilities()
    provider_info = capabilities.get(provider)
    if provider_info is None:
        return {
            "provider": provider,
            "supported": False,
            "scan_available": False,
            "products": discovery_catalog(),
        }
    if provider_info.get("status") != "active":
        return {
            "provider": provider,
            "supported": True,
            "adapter_status": provider_info.get("status"),
            "scan_available": False,
            "products": discovery_catalog(),
        }

    repo_key, head_sha = legacy._repo_head_identity(body.repo)
    return {
        "provider": provider,
        "supported": True,
        "adapter_status": "active",
        "reachable": bool(repo_key and head_sha),
        "repository": repo_key or body.repo,
        "commit_sha": head_sha,
        "scan_available": bool(head_sha),
        "products": discovery_catalog(),
    }


@app.post("/v1/repoguard/verify")
def verify_commit(body: VerifyCommitRequest):
    provider = _require_active_provider(body.provider)
    if provider != "github":
        raise HTTPException(status_code=501, detail={"error": "PROVIDER_ADAPTER_NOT_ACTIVE", "provider": provider})
    repo_key, current_sha = legacy._repo_head_identity(body.repo)
    matched = bool(current_sha and current_sha == body.expected_commit_sha)
    record_event(
        "product_fulfilled",
        status_code=200,
        network=X402_NETWORK,
        detail={"sku": "verify_commit", "repository": repo_key or body.repo, "matches": matched},
    )
    return {
        "product": "verify_commit",
        "price_usd": get_product("verify_commit").price_usd,
        "provider": provider,
        "repository": repo_key or body.repo,
        "expected_commit_sha": body.expected_commit_sha,
        "current_commit_sha": current_sha,
        "matches": matched,
    }


@app.post("/v1/repoguard/safe-to-ship")
def safe_to_ship(body: RepoRequest):
    scan = _run_canonical_scan(body, "safe_to_ship")
    return {
        "product": "safe_to_ship",
        "price_usd": get_product("safe_to_ship").price_usd,
        "provider": scan["provider"],
        "repository": scan["repository"],
        **safe_to_ship_view(scan["result"], scan["provenance"]),
    }


@app.post("/v1/repoguard/scan")
def repo_scan(body: RepoRequest):
    scan = _run_canonical_scan(body, "repo_scan")
    return {
        "service": "RepoGuard",
        "product": "repo_scan",
        "price_usd": get_product("repo_scan").price_usd,
        "network": X402_NETWORK,
        "cache": {
            "hit": scan["cache_hit"],
            "repoHeadSha": scan["head_sha"],
            "ttlSeconds": legacy._CACHE_TTL_SECONDS,
        },
        "provenance": scan["provenance"],
        "result": scan["result"],
    }


@app.post("/v1/repoguard/explain")
def explain_findings(body: RepoRequest):
    scan = _run_canonical_scan(body, "explain_findings")
    return {
        "product": "explain_findings",
        "price_usd": get_product("explain_findings").price_usd,
        "provider": scan["provider"],
        "repository": scan["repository"],
        "provenance": scan["provenance"],
        **remediation_view(scan["result"], scan["provenance"]["scan_id"]),
    }


@app.post("/v1/repoguard/attest")
def attest_scan(body: RepoRequest):
    scan = _run_canonical_scan(body, "attest_scan")
    return {
        "product": "attest_scan",
        "price_usd": get_product("attest_scan").price_usd,
        "provider": scan["provider"],
        "repository": scan["repository"],
        "attestation": build_attestation(scan["provenance"]),
    }


if X402_PAY_TO:
    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=X402_FACILITATOR_URL))
    x402_server = x402ResourceServer(facilitator)
    x402_server.register(X402_NETWORK, ExactEvmServerScheme())

    paid_routes: dict[str, RouteConfig] = {}
    for product in PRODUCTS.values():
        if not product.paid:
            continue
        paid_routes[f"POST {product.endpoint}"] = RouteConfig(
            accepts=[
                PaymentOption(
                    scheme="exact",
                    pay_to=X402_PAY_TO,
                    price=f"${product.price_usd}",
                    network=X402_NETWORK,
                )
            ],
            mime_type="application/json",
            description=product.purpose,
        )

    app.add_middleware(PaymentMiddlewareASGI, routes=paid_routes, server=x402_server)


# Preserve the existing human-facing RepoGuard application and legacy routes.
# The new /v1/repoguard commerce routes above are registered first and win.
app.mount("/", legacy.app)
