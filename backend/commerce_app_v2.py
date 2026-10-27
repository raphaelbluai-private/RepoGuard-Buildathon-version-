from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import app as legacy
from commerce_contracts import provider_capabilities, remediation_view, safe_to_ship_view
from commerce_telemetry import record_event
from operational_alerts import emit_alert
from operational_readiness import operational_readiness
from runtime_identity import public_runtime_identity_view, require_runtime_identity, runtime_identity_view
from payment_operations import (
    CHALLENGED,
    FULFILLED,
    FULFILLMENT_FAILED_RETRIABLE,
    FULFILLMENT_FAILED_TERMINAL,
    FULFILLMENT_STARTED,
    PRESENTED,
    RECEIPT_ISSUED,
    SETTLED,
    SETTLEMENT_FAILED_RETRIABLE,
    SETTLEMENT_PENDING,
    VERIFIED,
    VERIFICATION_REJECTED,
    PaymentOperationError,
    begin_transaction,
    bind_presented_payment,
    canonical_request_hash,
    current_transaction_id,
    decode_settlement_header,
    get_by_idempotency,
    get_transaction,
    issue_receipt,
    metrics as payment_metrics,
    payment_proof_digest,
    record_control_event,
    reset_current_transaction,
    set_current_transaction,
    transition,
)
from launch_security import (
    ScanConcurrencyGate,
    cors_origins,
    is_legacy_route_blocked,
    is_public_preview_only,
    provider_allowed_in_launch,
)
from product_catalog import PRODUCTS, discovery_catalog, get_product
from persistent_scan_cache import get as persistent_cache_get, put as persistent_cache_put, stats as persistent_cache_stats
from provenance import build_attestation, build_provenance
from provider_scanner import scan_repo_provider
from source_adapters import credentials_configured, normalize_provider_key, repo_head_identity

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer
from starlette.middleware.base import BaseHTTPMiddleware


app = FastAPI(title="RepoGuard Agent Commerce API", version="2.2.0")


@app.on_event("startup")
def validate_runtime_identity_on_startup() -> None:
    require_runtime_identity()

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
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    response.headers["Cache-Control"] = "no-store"
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
        "runtime_identity": public_runtime_identity_view(),
        "persistent_cache": persistent_cache_stats(),
    }


class RepoRequest(BaseModel):
    repo: str = Field(min_length=1, max_length=2048)
    provider: str = Field(default="github", min_length=1, max_length=64)


class VerifyCommitRequest(RepoRequest):
    expected_commit_sha: str = Field(min_length=7, max_length=128)


_PAID_SKU_BY_PATH = {
    product.endpoint: product.sku for product in PRODUCTS.values() if product.paid
}


def _transaction_id(request: Request | None) -> str | None:
    if request is None:
        return None
    return getattr(request.state, "payment_transaction_id", None)


def _begin_fulfillment(request: Request | None) -> None:
    transaction_id = _transaction_id(request)
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if tx is None:
        raise HTTPException(status_code=500, detail={"error": "PAYMENT_TRANSACTION_MISSING"})
    if tx.state == PRESENTED:
        transition(transaction_id, VERIFIED)
        tx = get_transaction(transaction_id)
    if tx and tx.state == VERIFIED:
        transition(transaction_id, FULFILLMENT_STARTED)


def _complete_fulfillment(request: Request | None, payload: dict[str, Any], *, cache_hit: bool | None = None) -> None:
    transaction_id = _transaction_id(request)
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if tx and tx.state == FULFILLMENT_STARTED:
        transition(
            transaction_id,
            FULFILLED,
            cache_hit=cache_hit,
            response_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        )


def _fail_fulfillment(request: Request | None, code: str, *, retryable: bool) -> None:
    transaction_id = _transaction_id(request)
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if tx and tx.state in {VERIFIED, FULFILLMENT_STARTED}:
        transition(
            transaction_id,
            FULFILLMENT_FAILED_RETRIABLE if retryable else FULFILLMENT_FAILED_TERMINAL,
            failure_code=code,
            retryable=retryable,
        )


class PaymentOperationsBoundary(BaseHTTPMiddleware):
    """Outer boundary that prevents duplicate charge/fulfillment before x402 runs."""

    async def dispatch(self, request: Request, call_next):
        sku = _PAID_SKU_BY_PATH.get(request.url.path) if request.method.upper() == "POST" else None
        if not sku or not X402_PAY_TO:
            return await call_next(request)

        product = get_product(sku)
        try:
            raw_body = await request.body()
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except (UnicodeDecodeError, ValueError):
            body = {"_invalid_json_sha256": hashlib.sha256(raw_body).hexdigest() if raw_body else ""}

        request_hash = canonical_request_hash(sku=sku, body=body)
        idempotency_key = (request.headers.get("idempotency-key") or "").strip() or None
        proof = request.headers.get("payment-signature") or request.headers.get("x-payment")
        proof_digest = payment_proof_digest(proof)

        if idempotency_key:
            existing = get_by_idempotency(idempotency_key)
            if existing is not None:
                if existing.request_hash != request_hash or existing.sku != sku:
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": "IDEMPOTENCY_CONFLICT",
                            "transaction_id": existing.transaction_id,
                        },
                    )
                if existing.state in {SETTLED, RECEIPT_ISSUED} and existing.response_json:
                    payload = json.loads(existing.response_json)
                    response = JSONResponse(status_code=200, content=payload)
                    response.headers["X-RepoGuard-Transaction-ID"] = existing.transaction_id
                    response.headers["X-RepoGuard-Idempotent-Replay"] = "true"
                    if existing.receipt_id:
                        response.headers["X-RepoGuard-Receipt-ID"] = existing.receipt_id
                    return response
                if existing.state in {PRESENTED, VERIFIED, FULFILLMENT_STARTED}:
                    response = JSONResponse(
                        status_code=409,
                        content={
                            "error": "TRANSACTION_IN_PROGRESS",
                            "transaction_id": existing.transaction_id,
                            "state": existing.state,
                        },
                    )
                    response.headers["Retry-After"] = "2"
                    return response
                if existing.state in {FULFILLED, SETTLEMENT_PENDING}:
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": "PAYMENT_RECONCILIATION_REQUIRED",
                            "transaction_id": existing.transaction_id,
                            "state": existing.state,
                            "message": "Do not submit another payment until settlement is reconciled.",
                        },
                    )

        transaction_id: str | None = None
        if proof_digest:
            try:
                tx = begin_transaction(
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    payment_digest=proof_digest,
                    sku=sku,
                    price_usd=product.price_usd,
                    network=X402_NETWORK,
                    facilitator_url=X402_FACILITATOR_URL,
                )
                if tx.state == CHALLENGED:
                    tx = bind_presented_payment(tx.transaction_id, proof_digest)
                transaction_id = tx.transaction_id
                request.state.payment_transaction_id = transaction_id
            except PaymentOperationError as exc:
                record_event(
                    "payment_replay_rejected" if exc.code == "REPLAY_REJECTED" else "payment_idempotency_conflict",
                    status_code=409,
                    network=X402_NETWORK,
                    detail={"sku": sku, "transaction_id": exc.transaction_id},
                )
                return JSONResponse(
                    status_code=409,
                    content={"error": exc.code, "transaction_id": exc.transaction_id},
                )

        context_token = set_current_transaction(transaction_id)
        try:
            response = await call_next(request)
        finally:
            reset_current_transaction(context_token)

        if not proof_digest and response.status_code == 402:
            try:
                tx = begin_transaction(
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    payment_digest=None,
                    sku=sku,
                    price_usd=product.price_usd,
                    network=X402_NETWORK,
                    facilitator_url=X402_FACILITATOR_URL,
                    challenged=True,
                )
                response.headers["X-RepoGuard-Transaction-ID"] = tx.transaction_id
                response.headers["X-RepoGuard-Idempotency-Key"] = tx.idempotency_key
            except PaymentOperationError:
                pass
            return response

        if transaction_id:
            settlement_value = response.headers.get("PAYMENT-RESPONSE") or response.headers.get("X-PAYMENT-RESPONSE")
            settlement = decode_settlement_header(settlement_value)
            tx = get_transaction(transaction_id)
            if settlement_value and tx and tx.state == FULFILLED:
                if bool(settlement.get("success", response.status_code < 400)):
                    tx = transition(transaction_id, SETTLEMENT_PENDING)
                    tx_hash = settlement.get("transaction") or settlement.get("transactionHash")
                    tx = transition(
                        transaction_id,
                        SETTLED,
                        transaction_hash=str(tx_hash) if tx_hash else None,
                        retryable=False,
                    )
                    tx = issue_receipt(transaction_id)
                    record_event(
                        "payment_receipt_issued",
                        status_code=response.status_code,
                        network=X402_NETWORK,
                        transaction_hash=tx.transaction_hash,
                        cache_hit=tx.cache_hit,
                        detail={"sku": sku, "transaction_id": transaction_id, "receipt_id": tx.receipt_id},
                    )
                else:
                    transition(
                        transaction_id,
                        SETTLEMENT_FAILED_RETRIABLE,
                        failure_code=str(settlement.get("errorReason") or settlement.get("error") or "SETTLEMENT_FAILED"),
                        retryable=True,
                    )
            elif tx and tx.state == FULFILLED and response.status_code >= 400:
                transition(
                    transaction_id,
                    SETTLEMENT_PENDING,
                    failure_code="SETTLEMENT_OUTCOME_UNKNOWN",
                    retryable=True,
                )
            elif tx and tx.state == PRESENTED and response.status_code == 402:
                transition(
                    transaction_id,
                    VERIFICATION_REJECTED,
                    failure_code="PAYMENT_VERIFICATION_REJECTED",
                    retryable=False,
                )

            tx = get_transaction(transaction_id)
            response.headers["X-RepoGuard-Transaction-ID"] = transaction_id
            if tx and tx.receipt_id:
                response.headers["X-RepoGuard-Receipt-ID"] = tx.receipt_id

        return response


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


def _run_canonical_scan(body: RepoRequest, sku: str, request: Request | None = None) -> dict[str, Any]:
    _begin_fulfillment(request)
    if not SCAN_CONCURRENCY_GATE.try_acquire():
        _fail_fulfillment(request, "SCAN_CAPACITY_EXHAUSTED", retryable=True)
        emit_alert(
            "SCAN_CAPACITY_EXHAUSTED",
            severity="WARNING",
            component="scanner",
            transaction_id=_transaction_id(request),
            retryable=True,
        )
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
    except HTTPException as exc:
        _fail_fulfillment(request, str((exc.detail or {}).get("error", "SCAN_FAILED")) if isinstance(exc.detail, dict) else "SCAN_FAILED", retryable=exc.status_code >= 500)
        raise
    except Exception as exc:
        _fail_fulfillment(request, type(exc).__name__, retryable=True)
        emit_alert(
            "SCAN_EXECUTION_EXCEPTION",
            severity="ERROR",
            component="scanner",
            transaction_id=_transaction_id(request),
            retryable=True,
            detail={"exception_type": type(exc).__name__},
        )
        raise
    finally:
        SCAN_CONCURRENCY_GATE.release()


def _run_canonical_scan_acquired(body: RepoRequest, sku: str) -> dict[str, Any]:
    provider = _require_active_provider(body.provider)
    started = time.monotonic()
    repo_key, head_sha, identity_url = _identity(provider, body.repo)

    cached = persistent_cache_get(repo_key, head_sha) if head_sha else None
    cache_hit = cached is not None

    if cache_hit:
        result = cached
    else:
        try:
            result = scan_repo_provider(provider, body.repo)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "SCAN_ERROR",
                    "provider": provider,
                    "message": f"Scan failed unexpectedly: {type(exc).__name__}",
                },
                headers={"Retry-After": "2"},
            ) from exc
        if head_sha and isinstance(result, dict) and result.get("ok"):
            persistent_cache_put(repo_key, head_sha, result)

    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail={"error": "INVALID_SCAN_RESULT", "provider": provider})
    if result.get("ok") is False:
        error_code = str(result.get("error") or "SCAN_FAILED")
        retryable = error_code in {"NETWORK_ERROR", "RATE_LIMIT", "GITHUB_ERROR", "PROVIDER_TIMEOUT", "SCAN_ERROR"}
        raise HTTPException(
            status_code=503 if retryable else 422,
            detail={"error": error_code, "message": result.get("message")},
            headers={"Retry-After": "2"} if retryable else None,
        )

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


@app.get("/v1/repoguard/operational-readiness", include_in_schema=False)
def internal_operational_readiness():
    if os.environ.get("REPOGUARD_INTERNAL", "").strip().lower() not in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
    return operational_readiness()


@app.get("/v1/repoguard/runtime-identity", include_in_schema=False)
def full_runtime_identity():
    if os.environ.get("REPOGUARD_INTERNAL", "").strip().lower() not in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
    return runtime_identity_view()


@app.get("/v1/repoguard/payment-operations/metrics", include_in_schema=False)
def payment_operations_metrics():
    if os.environ.get("REPOGUARD_INTERNAL", "").strip().lower() not in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
    return {
        "service": "RepoGuard",
        "scope": "payment_operations",
        "network": X402_NETWORK,
        "metrics": payment_metrics(),
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
def verify_commit(body: VerifyCommitRequest, request: Request):
    _begin_fulfillment(request)
    try:
        provider = _require_active_provider(body.provider)
        repo_key, current_sha, repository_url = _identity(provider, body.repo)
        matched = bool(current_sha and current_sha == body.expected_commit_sha)
        repository = repo_key.split(":", 1)[-1]
        payload = {
            "product": "verify_commit",
            "price_usd": get_product("verify_commit").price_usd,
            "provider": provider,
            "repository": repository,
            "repository_url": repository_url,
            "expected_commit_sha": body.expected_commit_sha,
            "current_commit_sha": current_sha,
            "matches": matched,
        }
        record_event(
            "product_fulfilled",
            status_code=200,
            network=X402_NETWORK,
            detail={"sku": "verify_commit", "provider": provider, "repository": repository, "matches": matched},
        )
        _complete_fulfillment(request, payload)
        return payload
    except HTTPException as exc:
        _fail_fulfillment(request, "VERIFY_COMMIT_FAILED", retryable=exc.status_code >= 500)
        raise


@app.post("/v1/repoguard/safe-to-ship")
def safe_to_ship(body: RepoRequest, request: Request):
    scan = _run_canonical_scan(body, "safe_to_ship", request)
    payload = {
        "product": "safe_to_ship",
        "price_usd": get_product("safe_to_ship").price_usd,
        "provider": scan["provider"],
        "repository": scan["repository"],
        **safe_to_ship_view(scan["result"], scan["provenance"]),
    }
    _complete_fulfillment(request, payload, cache_hit=scan["cache_hit"])
    return payload


@app.post("/v1/repoguard/scan")
def repo_scan(body: RepoRequest, request: Request):
    scan = _run_canonical_scan(body, "repo_scan", request)
    payload = {
        "service": "RepoGuard",
        "product": "repo_scan",
        "price_usd": get_product("repo_scan").price_usd,
        "network": X402_NETWORK,
        "provider": scan["provider"],
        "cache": {
            "hit": scan["cache_hit"],
            "repoHeadSha": scan["head_sha"],
            "ttlSeconds": persistent_cache_stats()["ttl_seconds"],
        },
        "provenance": scan["provenance"],
        "result": scan["result"],
    }
    _complete_fulfillment(request, payload, cache_hit=scan["cache_hit"])
    return payload


@app.post("/v1/repoguard/explain")
def explain_findings(body: RepoRequest, request: Request):
    scan = _run_canonical_scan(body, "explain_findings", request)
    payload = {
        "product": "explain_findings",
        "price_usd": get_product("explain_findings").price_usd,
        "provider": scan["provider"],
        "repository": scan["repository"],
        "provenance": scan["provenance"],
        **remediation_view(scan["result"], scan["provenance"]["scan_id"]),
    }
    _complete_fulfillment(request, payload, cache_hit=scan["cache_hit"])
    return payload


@app.post("/v1/repoguard/attest")
def attest_scan(body: RepoRequest, request: Request):
    scan = _run_canonical_scan(body, "attest_scan", request)
    payload = {
        "product": "attest_scan",
        "price_usd": get_product("attest_scan").price_usd,
        "provider": scan["provider"],
        "repository": scan["repository"],
        "attestation": build_attestation(scan["provenance"]),
    }
    _complete_fulfillment(request, payload, cache_hit=scan["cache_hit"])
    return payload


async def _x402_after_verify(context) -> None:
    transaction_id = current_transaction_id()
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if tx and tx.state == PRESENTED:
        transition(transaction_id, VERIFIED)


async def _x402_verify_failure(context) -> None:
    transaction_id = current_transaction_id()
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if tx and tx.state == PRESENTED:
        transition(
            transaction_id,
            VERIFICATION_REJECTED,
            failure_code="PAYMENT_VERIFICATION_REJECTED",
            retryable=False,
        )
        emit_alert(
            "PAYMENT_VERIFICATION_REJECTED",
            severity="WARNING",
            component="payments",
            transaction_id=transaction_id,
            retryable=False,
        )


async def _x402_before_settle(context) -> None:
    transaction_id = current_transaction_id()
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if tx and tx.state == FULFILLED:
        transition(transaction_id, SETTLEMENT_PENDING)


async def _x402_after_settle(context) -> None:
    transaction_id = current_transaction_id()
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if not tx or tx.state != SETTLEMENT_PENDING:
        return
    result = getattr(context, "result", None)
    transaction_hash = getattr(result, "transaction", None) or getattr(result, "transaction_hash", None)
    tx = transition(
        transaction_id,
        SETTLED,
        transaction_hash=str(transaction_hash) if transaction_hash else None,
        retryable=False,
    )
    tx = issue_receipt(transaction_id)
    record_event(
        "payment_receipt_issued",
        status_code=200,
        network=X402_NETWORK,
        transaction_hash=tx.transaction_hash,
        cache_hit=tx.cache_hit,
        detail={"sku": tx.sku, "transaction_id": transaction_id, "receipt_id": tx.receipt_id},
    )


async def _x402_settle_failure(context) -> None:
    transaction_id = current_transaction_id()
    if not transaction_id:
        return
    tx = get_transaction(transaction_id)
    if not tx or tx.state != SETTLEMENT_PENDING:
        return
    error = getattr(context, "error", None) or getattr(context, "exception", None)
    message = str(error or "settlement failure")
    if "timeout" in message.lower():
        emit_alert(
            "SETTLEMENT_OUTCOME_UNKNOWN",
            severity="ERROR",
            component="payments",
            transaction_id=transaction_id,
            retryable=False,
            detail={"reconciliation_required": True},
        )
        record_control_event(
            "settlement_timeout_indeterminate",
            transaction_id=transaction_id,
            detail={"message": message[:256]},
        )
        return
    transition(
        transaction_id,
        SETTLEMENT_FAILED_RETRIABLE,
        failure_code="FACILITATOR_SETTLEMENT_FAILED",
        retryable=True,
    )
    emit_alert(
        "FACILITATOR_SETTLEMENT_FAILED",
        severity="ERROR",
        component="payments",
        transaction_id=transaction_id,
        retryable=True,
    )


if X402_PAY_TO:
    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=X402_FACILITATOR_URL))
    x402_server = x402ResourceServer(facilitator)
    x402_server.register(X402_NETWORK, ExactEvmServerScheme())
    x402_server.on_after_verify(_x402_after_verify)
    x402_server.on_verify_failure(_x402_verify_failure)
    x402_server.on_before_settle(_x402_before_settle)
    x402_server.on_after_settle(_x402_after_settle)
    x402_server.on_settle_failure(_x402_settle_failure)

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
    app.add_middleware(PaymentOperationsBoundary)


app.mount("/", legacy.app)
