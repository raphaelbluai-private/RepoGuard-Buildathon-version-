"""RepoGuard production API composition.

Runs the existing FastAPI application unchanged, adds the stable machine
contract, x402 payment boundary, discovery metadata, and commerce telemetry.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app import ScanBody, _client_ip, _enforce, app
from commerce_telemetry import CommerceTelemetryMiddleware, record_scan_served, summary
from commercial import commercial_scan, github_auth_configured
from x402_payments import configure_x402, public_payment_metadata, x402_enabled


_X402_STATE = None


@app.middleware("http")
async def block_legacy_free_scan_when_paid(request: Request, call_next):
    """Prevent the legacy scanner from bypassing the paid machine route."""
    if (
        x402_enabled()
        and request.method.upper() == "POST"
        and request.url.path == "/api/scan"
    ):
        return JSONResponse(
            status_code=410,
            content={
                "ok": False,
                "error": "COMMERCIAL_ROUTE_REQUIRED",
                "message": "RepoGuard scans are available through the paid /v1/scan route.",
                "route": "/v1/scan",
            },
        )
    return await call_next(request)


@app.get("/v1/health")
def commercial_health():
    x402_state = _X402_STATE or {
        "enabled": False,
        "protected": False,
        "network": None,
        "price": None,
        "facilitator": None,
        "bazaar": False,
    }
    return {
        "status": "ok",
        "service": "repoguard",
        "version": "1.0",
        "github_authenticated": github_auth_configured(),
        "x402": x402_state,
        "commerce": summary(),
    }


@app.get("/.well-known/x402")
def x402_service_manifest():
    """RepoGuard-owned machine-readable discovery fallback.

    Bazaar remains the canonical x402 discovery mechanism. This well-known
    manifest gives agents a stable, documented bootstrap path independent of
    any third-party indexer.
    """
    return {
        "service": "RepoGuard",
        "description": "Deterministic Safe-to-Ship analysis for public GitHub repositories.",
        "version": "1.0",
        "input": {
            "content_type": "application/json",
            "schema": {
                "type": "object",
                "properties": {"repo": {"type": "string"}},
                "required": ["repo"],
            },
        },
        "payment": public_payment_metadata(),
    }


@app.get("/v1/commerce/summary")
def commerce_summary():
    """Public aggregate transaction telemetry; contains no payment secrets."""
    return {"service": "repoguard", "commerce": summary()}


@app.post("/v1/scan")
def v1_scan(body: ScanBody, request: Request):
    ip = _client_ip(request)
    _enforce(f"commercial_scan:{ip}", limit=30, window=60, lockout_secs=60)
    payload, status_code = commercial_scan(body.repo)
    if status_code == 200 and payload.get("ok"):
        record_scan_served(cache_hit=bool(payload.get("cache_hit")), status_code=200)
    return JSONResponse(status_code=status_code, content=payload)


# Payment middleware is installed after routes are registered. Telemetry is
# installed last so it observes the final 402/settlement response emitted by x402.
_X402_STATE = configure_x402(app)
app.add_middleware(CommerceTelemetryMiddleware)
