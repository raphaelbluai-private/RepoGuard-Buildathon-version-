"""RepoGuard production API composition.

Runs the existing FastAPI application unchanged and adds the stable machine
contract used by x402 in Sprint 001.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app import ScanBody, _client_ip, _enforce, app
from commercial import commercial_scan, github_auth_configured


@app.get("/v1/health")
def commercial_health():
    return {
        "status": "ok",
        "service": "repoguard",
        "version": "1.0",
        "github_authenticated": github_auth_configured(),
    }


@app.post("/v1/scan")
def v1_scan(body: ScanBody, request: Request):
    ip = _client_ip(request)
    _enforce(f"commercial_scan:{ip}", limit=30, window=60, lockout_secs=60)
    payload, status_code = commercial_scan(body.repo)
    return JSONResponse(status_code=status_code, content=payload)
