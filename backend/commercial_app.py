"""RepoGuard production API composition.

Runs the existing FastAPI application unchanged, adds the stable machine
contract, and installs the Sprint 001 x402 payment boundary when enabled.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app import ScanBody, _client_ip, _enforce, app
from commercial import commercial_scan, github_auth_configured
from x402_payments import configure_x402, x402_enabled


_X402_STATE = None


@app.middleware("http")
async def block_legacy_free_scan_when_paid(request: Request, call_next):
    """Prevent the legacy scanner from bypassing the paid machine route.

    `/api/scan` remains available while x402 is disabled for demo/development
    compatibility. Once commerce is enabled, equivalent scanner capability must
    go through `/v1/scan`, where the x402 middleware issues the payment challenge.
    """
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
    }
    return {
        "status": "ok",
        "service": "repoguard",
        "version": "1.0",
        "github_authenticated": github_auth_configured(),
        "x402": x402_state,
    }


@app.post("/v1/scan")
def v1_scan(body: ScanBody, request: Request):
    ip = _client_ip(request)
    _enforce(f"commercial_scan:{ip}", limit=30, window=60, lockout_secs=60)
    payload, status_code = commercial_scan(body.repo)
    return JSONResponse(status_code=status_code, content=payload)


# Install payment middleware only after all routes have been registered. The
# configuration is fail-closed when REPOGUARD_X402_ENABLED=1.
_X402_STATE = configure_x402(app)
