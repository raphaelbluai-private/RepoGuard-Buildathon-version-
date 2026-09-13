from __future__ import annotations

import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import app as legacy
from commerce_contracts import provider_capabilities, remediation_view, safe_to_ship_view
from commerce_telemetry import record_event
from launch_security import (
    ScanConcurrencyGate,
    cors_origins,
    is_legacy_route_blocked,
    is_public_preview_only,
    provider_allowed_in_launch,
)
from product_catalog import PRODUCTS, discovery_catalog, get_product
from provenance import build_attestation, build_provenance
from provider_scanner import scan_repo_provider
from source_adapters import credentials_configured, normalize_provider_key, repo_head_identity

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer


app = FastAPI(title="RepoGuard Agent Commerce API", version="2.2.0")

X402_NETWORK = os.environ.get("REPOGUARD_X402_NETWORK", getattr(legacy, "X402_NETWORK", "eip155:84532"))
X402_PAY_TO = os.environ.get("REPOGUARD_PAY_TO")
X402_FACILITATOR_URL = os.environ.get("REPOGUARD_X402_FACILITATOR_URL", "https://x402.org/facilitator")
MAX_REQUEST_BYTES = int(os.environ.get("REPOGUARD_MAX_REQUEST_BYTES", "65536"))
MAX_CONCURRENT_SCANS = int(os.environ.get("REPOGUARD_MAX_CONCURRENT_SCANS", "4"))
SCAN_CONCURRENCY_GATE = ScanConcurrencyGate(MAX_CONCURRENT_SCANS)

_CORS_HEADERS = (
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-allow-credentials",
    "access-control-expose-headers",
)


def _apply_hardened_cors(request: Request, response):
    for header in _CORS_HEADERS:
        if header in response.headers:
            del response.headers[header]

    origin = request.headers.get("origin")
    approved = cors_origins()
    if origin and origin in approved:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers[
            "Access-Control-Allow-Headers"
        ] = "Content-Type, Authorization, Payment-Signature, PAYMENT-SIGNATURE"
        vary = response.headers.get("Vary")
        response.headers["Vary"] = f"{vary}, Origin" if vary else "Origin"
    return response


def _apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def launch_security_boundary(request: Request, call_next):
    if is_legacy_route_blocked(request.url.path):
        return _apply_security_headers(JSONResponse(
            status_code=410,
            content={
                "error": "LEGACY_ROUTE_DISABLED",
                "message": "This legacy/demo route is disabled on the hardened commerce service.",
            },
        ))

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                return _apply_security_headers(JSONResponse(
                    status_code=413,
                    content={"error": "REQUEST_TOO_LARGE", "max_bytes": MAX_REQUEST_BYTES},
                ))
        except ValueError:
            return _apply_security_headers(JSONResponse(
                status_code=400,
                content={"error": "INVALID_CONTENT_LENGTH"},
            ))

    response = await call_next(request)
    response = _apply_hardened_cors(request, response)
    return _apply_security_headers(response)


@app.get("/v1/health", include_in_schema=False)
def v1_health():
    return {
        "status": "ok",
        "service": "RepoGuard",
        "api_version": "2.2.0",
        "provider_adapters": "active",
        "public_preview_only": is_public_preview_only(),
        "x402_configured": bool(X402_PAY_TO),
        "max_concurrent_scans": MAX_CONCURRENT_SCANS,
    }


class RepoRequest(BaseModel):
    repo: str = Field(min_length=1, max_length=2048)
    provider: str = Field(default="github", min_length=1, max_length=64)


class VerifyCommitRequest(RepoRequest):
    expected_commit_sha: str = Field(min_length=7, max_length=128)


def _provider_key(provider: str) -> str:
    return normalize_provider_key(provider)


def _require_active_provider(provider: str) -> str:
    key = _provider_key(provider)
    capabilities = provider_capabilities()
    if key not in capabilities:
        raise HTTPException(
            status_code=422,
            detail={"error": "UNSUPPORTED_PROVIDER", "provider": key, "providers": capabilities},
        )
    provider_info = capabilities[key]
    if provider_info.get("status") != "active":
        raise HTTPException(
            status_code=501,
            detail={
                "error": "PROVIDER_ADAPTER_NOT_ACTIVE",
                "provider": key,
                "status": provider_info.get("status"),
            },
        )
    if not provider_allowed_in_launch(provider_info):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PUBLIC_PREVIEW_ONLY",
                "provider": key,
                "message": "Authenticated/private provider access is disabled for the current launch scope.",
            },
        )
    return key


def _identity(provider: str, repo: str) -> tuple[str, str | None, str]:
    try:
        return repo_head_identity(provider, repo)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "INVALID_REPOSITORY", "message": str(exc)}) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail={"error": "PROVIDER_TIMEOUT", "provider": provider}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"error": "ADAPTER_RUNTIME_ERROR", "message": str(exc)}) from exc


def _run_canonical_scan(body: RepoRequest, sku: str) -> dict[str, Any]:
    if not SCAN_CONCURRENCY_GATE.try_acquire():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SCAN_CAPACITY_EXHAUSTED",
                "message": "RepoGuard scan capacity is temporarily full. Retry shortly.",
            },
            headers={"Retry-After": "2"},
        )
    try:
        return _run_canonical_scan_acquired(body, sku)
    finally:
        SCAN_CONCURRENCY_GATE.release()


def _run_canonical_scan_acquired(body: RepoRequest, sku: str) -> dict[str, Any]:
    provider = _require_active_provider(body.provider)
    started = time.monotonic()
    repo_key, head_sha, identity_url = _identity(provider, body.repo)

    cached = legacy._cache_get(repo_key, head_sha) if head_sha else None
    cache_hit = cached is not None

    if cache_hit:
        result = cached
    else:
        try:
            result = scan_repo_provider(provider, body.repo)
        except Exception as exc:
            result = {
                "ok": False,
                "error": "SCAN_ERROR",
                "provider": provider,
                "message": f"Scan failed unexpectedly: {type(exc).__name__}",
            }
        if head_sha and isinstance(result, dict) and result.get("ok"):
            legacy._cache_put(repo_key, head_sha, result)

    if not isinstance(result, dict):
        result = {"ok": False, "error": "INVALID_SCAN_RESULT", "provider": provider}

    result_repo = result.get("repo") if isinstance(result.get("repo"), dict) else {}
    repository = result_repo.get("fullName") or repo_key.split(":", 1)[-1] or body.repo
    repository_url = result_repo.get("url") or result.get("repository_url") or identity_url
    effective_sha = result.get("commitSha") or head_sha

    provenance = build_provenance(
        provider=provider,
        repository=repository,
        repository_url=repository_url,
        commit_sha=effective_sha,
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
            "provider": provider,
            "repository": repository,
            "scan_id": provenance["scan_id"],
            "latency_ms": latency_ms,
        },
    )

    return {
        "provider": provider,
        "repository": repository,
        "head_sha": effective_sha,
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
        "public_preview_only": is_public_preview_only(),
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

    if not provider_allowed_in_launch(provider_info):
        return {
            "provider": provider,
            "supported": True,
            "adapter_status": "active",
            "scan_available": False,
            "error": "PUBLIC_PREVIEW_ONLY",
            "message": "This provider requires authenticated/private access and is disabled for the current launch scope.",
            "provider_info": provider_info,
            "products": discovery_catalog(),
        }

    if provider_info.get("auth_required") and not credentials_configured(provider):
        return {
            "provider": provider,
            "supported": True,
            "adapter_status": "active",
            "credentials_required": True,
            "credentials_configured": False,
            "scan_available": False,
            "provider_info": provider_info,
            "products": discovery_catalog(),
        }

    try:
        repo_key, head_sha, repository_url = repo_head_identity(provider, body.repo)
        repository = repo_key.split(":", 1)[-1]
        return {
            "provider": provider,
            "supported": True,
            "adapter_status": "active",
            "reachable": bool(head_sha),
            "repository": repository,
            "repository_url": repository_url,
            "commit_sha": head_sha,
            "scan_available": bool(head_sha),
            "provider_info": provider_info,
            "products": discovery_catalog(),
        }
    except ValueError as exc:
        return {
            "provider": provider,
            "supported": True,
            "adapter_status": "active",
            "reachable": False,
            "scan_available": False,
            "error": "INVALID_REPOSITORY",
            "message": str(exc),
            "provider_info": provider_info,
            "products": discovery_catalog(),
        }
    except (TimeoutError, RuntimeError) as exc:
        return {
            "provider": provider,
            "supported": True,
            "adapter_status": "active",
            "reachable": False,
            "scan_available": False,
            "error": "PROVIDER_UNAVAILABLE",
            "message": str(exc),
            "provider_info": provider_info,
            "products": discovery_catalog(),
        }


@app.post("/v1/repoguard/verify")
def verify_commit(body: VerifyCommitRequest):
    provider = _require_active_provider(body.provider)
    repo_key, current_sha, repository_url = _identity(provider, body.repo)
    matched = bool(current_sha and current_sha == body.expected_commit_sha)
    repository = repo_key.split(":", 1)[-1]
    record_event(
        "product_fulfilled",
        status_code=200,
        network=X402_NETWORK,
        detail={"sku": "verify_commit", "provider": provider, "repository": repository, "matches": matched},
    )
    return {
        "product": "verify_commit",
        "price_usd": get_product("verify_commit").price_usd,
        "provider": provider,
        "repository": repository,
        "repository_url": repository_url,
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
        "provider": scan["provider"],
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


app.mount("/", legacy.app)
