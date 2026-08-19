"""RepoGuard production API composition.

Runs the existing FastAPI application unchanged, adds the stable machine
contract, and installs the Sprint 001 x402 payment boundary when enabled.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app import ScanBody, _client_ip, _enforce, app
from commercial import commercial_scan, github_auth_configured
from x402_payments import configure_x402


_X402_STATE = None


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


# Install payment middleware only after all routes have been registered.  The
# configuration is fail-closed when REPOGUARD_X402_ENABLED=1.
_X402_STATE = configure_x402(app)
