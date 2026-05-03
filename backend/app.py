"""
RepoGuard Backend — FastAPI
Includes thread-safe sliding-window rate limiting + lockout protections.
All limits are enforced in-process (no external dependency required).
"""

import os
import threading
import time
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scanner import scan_repo

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
# Pure stdlib, thread-safe, sliding-window implementation.
# Keys are namespaced strings (e.g. "otp_req:ip:1.2.3.4").

class _RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._windows: dict = defaultdict(list)      # key → [monotonic timestamps]
        self._lockouts: dict = {}                     # key → expiry timestamp
        self._failed_auth: dict = defaultdict(int)   # email → failed verify count

    def _prune(self, key: str, window: int, now: float):
        cutoff = now - window
        self._windows[key] = [t for t in self._windows[key] if t > cutoff]

    def is_locked_out(self, key: str) -> bool:
        with self._lock:
            exp = self._lockouts.get(key)
            if exp is None:
                return False
            if time.monotonic() < exp:
                return True
            del self._lockouts[key]
            return False

    def remaining_lockout(self, key: str) -> int:
        with self._lock:
            exp = self._lockouts.get(key, 0.0)
            return max(0, int(exp - time.monotonic()))

    def check_and_record(self, key: str, limit: int, window: int) -> bool:
        """Returns True if the request is allowed; False if rate-limited."""
        with self._lock:
            now = time.monotonic()
            self._prune(key, window, now)
            if len(self._windows[key]) >= limit:
                return False
            self._windows[key].append(now)
            return True

    def lockout(self, key: str, duration: int):
        with self._lock:
            self._lockouts[key] = time.monotonic() + duration

    def record_bad_verify(self, email: str, max_failures: int = 5, lockout_duration: int = 300) -> bool:
        """
        Record a failed code-verify attempt for an email.
        Returns False (and locks the account) once max_failures is reached.
        """
        lock_key = f"auth_lock:{email}"
        with self._lock:
            self._failed_auth[email] += 1
            if self._failed_auth[email] >= max_failures:
                self._lockouts[lock_key] = time.monotonic() + lockout_duration
                self._failed_auth[email] = 0
                return False
            return True

    def reset_bad_verify(self, email: str):
        with self._lock:
            self._failed_auth[email] = 0

    def stats(self) -> dict:
        with self._lock:
            now = time.monotonic()
            active_lockouts = {k: round(exp - now, 1) for k, exp in self._lockouts.items() if exp > now}
            return {
                "active_lockout_keys": active_lockouts,
                "active_lockout_count": len(active_lockouts),
                "tracked_email_failures": dict(self._failed_auth),
                "tracked_rate_windows": len(self._windows),
            }


limiter = _RateLimiter()


def _client_ip(request: Request) -> str:
    # Trust the direct socket address. We intentionally do NOT honour
    # X-Forwarded-For because, without a verified trusted-proxy chain, any
    # client could spoof the header to bypass per-IP rate limits and burn
    # through GitHub's unauthenticated API quota for everyone else.
    return request.client.host if request.client else "unknown"


def _enforce(key: str, limit: int, window: int, lockout_secs: int = 0):
    """
    Check rate limit + optional lockout, raise HTTP 429 if exceeded.
    lockout_secs > 0: trigger a lockout after the first window overflow.
    """
    if lockout_secs and limiter.is_locked_out(key):
        wait = limiter.remaining_lockout(key)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "locked_out",
                "message": "Too many requests. You are locked out.",
                "retry_after_seconds": wait,
            },
            headers={"Retry-After": str(wait), "X-RateLimit-Locked": "true"},
        )

    allowed = limiter.check_and_record(key, limit, window)
    if not allowed:
        if lockout_secs:
            limiter.lockout(key, lockout_secs)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": f"Rate limit exceeded: max {limit} requests per {window}s.",
            },
            headers={
                "Retry-After": str(window),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": str(window),
            },
        )


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Data store ───────────────────────────────────────────────────────────────

events: list = []
repos: list = [
    {"id": "1", "source": "GitHub",    "name": "api-service",  "issue": "Monitoring active", "severity": "none", "status": "secure",  "before": 72, "after": 72, "checked": "now"},
    {"id": "2", "source": "GitLab",    "name": "frontend",     "issue": "Monitoring active", "severity": "none", "status": "secure",  "before": 88, "after": 88, "checked": "now"},
    {"id": "3", "source": "Bitbucket", "name": "worker-queue", "issue": "Monitoring active", "severity": "none", "status": "secure",  "before": 94, "after": 94, "checked": "now"},
]
system_status: dict = {"status": "monitoring"}
login_codes: Dict[str, str] = {}

_START_TIME = time.monotonic()


class EmailBody(BaseModel):
    email: str

class VerifyBody(BaseModel):
    email: str
    code: str


def stamp(message: str):
    events.append({"message": message, "time": datetime.now().isoformat()})
    if len(events) > 100:            # cap unbounded growth
        del events[:-100]


def calculate_global_compliance():
    if not repos:
        return {"before": 100, "after": 100}
    return {
        "before": round(sum(r["before"] for r in repos) / len(repos)),
        "after":  round(sum(r["after"]  for r in repos) / len(repos)),
    }


# ─── Health & internal monitoring ─────────────────────────────────────────────

@app.get("/api/health")
def health():
    """
    Liveness probe — no rate limit.
    Returns uptime, memory, and a simple ok/degraded status.
    """
    try:
        import resource
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except Exception:
        mem_kb = None

    return {
        "status": "ok",
        "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
        "timestamp": datetime.now().isoformat(),
        "memory_kb": mem_kb,
    }


@app.get("/api/_internal/rate-stats")
def rate_stats(request: Request):
    """
    Exposes rate-limiter internals for test reporting.
    Staging / internal use only — must NOT be reachable in production.

    Gated on env var REPOGUARD_INTERNAL=1 (only set in dev / CI). In any other
    environment this returns 404 so callers can't tell the endpoint exists.
    """
    if os.environ.get("REPOGUARD_INTERNAL") != "1":
        raise HTTPException(status_code=404)
    return limiter.stats()


# ─── Live-data polling endpoints ──────────────────────────────────────────────
# These are intentionally not rate-limited at the app layer; they are cheap
# in-memory reads.  DoS / flood protection for these belongs at the
# infrastructure layer (reverse proxy, WAF).

@app.get("/api/events")
def get_events():
    return events[-6:]


@app.get("/api/repos")
def get_repos():
    return repos


@app.get("/api/compliance")
def get_compliance():
    return calculate_global_compliance()


@app.get("/api/system-status")
def get_system_status():
    return system_status


# ─── Boot / policy-gate verification ──────────────────────────────────────────
# Rate limited: 30 req / 60 s per IP.
# Lockout after overflow: 120 s.
# Rationale: one legitimate browser tab hits this once on boot, not repeatedly.

@app.get("/api/repoguard/verify")
def verify_system(request: Request, project_id: Optional[str] = None):
    ip = _client_ip(request)
    _enforce(f"boot_verify:{ip}", limit=30, window=60, lockout_secs=120)

    t0 = time.time()
    checks = {
        "auth":        {"ok": True, "note": "demo session accepted"},
        "permissions": {"ok": True, "role": "operator"},
        "project":     {"ok": True, "project_id": project_id or "default"},
        "services":    {"db": True, "api": True, "enforcement_engine": True},
        "policy":      {"ok": True, "policy": "standard"},
    }
    all_passed = all(
        (v["ok"] if isinstance(v, dict) and "ok" in v else all(v.values()))
        for v in checks.values()
    )
    return {
        "status": "secure" if all_passed else "blocked",
        "checks": checks,
        "message": "Integrity verified — access granted" if all_passed else "Integrity failure detected",
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }


# ─── Auth endpoints ───────────────────────────────────────────────────────────
# Tightest limits — these are the primary brute-force / spam targets.

@app.post("/api/auth/request-code")
def request_code(body: EmailBody, request: Request):
    """
    Send a 6-digit OTP to the given email.
    Limits:
      • 5 requests / 60 s per source IP  → lockout 300 s
      • 3 requests / 60 s per email address → lockout 300 s
    """
    ip = _client_ip(request)
    _enforce(f"otp_req:ip:{ip}",             limit=5, window=60, lockout_secs=300)
    _enforce(f"otp_req:email:{body.email}",  limit=3, window=60, lockout_secs=300)

    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    login_codes[body.email] = code
    return {"sent": True, "email": body.email, "demo_code": code}


@app.post("/api/auth/verify-code")
def verify_code(body: VerifyBody, request: Request):
    """
    Verify a submitted OTP code.
    Limits:
      • 10 requests / 60 s per source IP  → lockout 300 s
      • 5 failed attempts per email        → account lockout 300 s
    Successful verify resets the failed-attempt counter.
    """
    ip = _client_ip(request)
    _enforce(f"auth_verify:ip:{ip}", limit=10, window=60, lockout_secs=300)

    lock_key = f"auth_lock:{body.email}"
    if limiter.is_locked_out(lock_key):
        wait = limiter.remaining_lockout(lock_key)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "account_locked",
                "message": "Account temporarily locked due to too many failed attempts.",
                "retry_after_seconds": wait,
            },
            headers={"Retry-After": str(wait)},
        )

    verified = login_codes.get(body.email) == body.code
    if verified:
        limiter.reset_bad_verify(body.email)
    else:
        still_ok = limiter.record_bad_verify(body.email, max_failures=5, lockout_duration=300)
        if not still_ok:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "account_locked",
                    "message": "Account locked for 5 minutes: too many failed verification attempts.",
                },
                headers={"Retry-After": "300"},
            )

    return {"verified": verified}


# ─── Demo control endpoints ────────────────────────────────────────────────────

@app.post("/api/demo-trigger")
def trigger():
    events.clear()
    system_status["status"] = "breach"

    repos[0].update(issue="Confirmed secret exposure", severity="critical", status="breach", before=72, after=72)
    repos[1].update(issue="Policy drift detected",     severity="warning",  status="warning", before=88, after=88)
    repos[2].update(issue="Minor config exposure",     severity="minor",    status="monitoring", before=94, after=94)

    stamp("Critical breach detected in GitHub / api-service")
    stamp("Auto enforcement triggered")
    stamp("Secret revoked and credentials invalidated")
    stamp("Pull request generated with secure patch")
    stamp("Merge blocked until compliance restored")

    return {"status": "ok"}


@app.post("/api/demo-resolve")
def resolve():
    for repo in repos:
        repo.update(status="resolved", issue="Repository returned to compliance", severity="none", after=100)
    system_status["status"] = "resolved"
    stamp("Repository returned to compliant state")

    def _auto_reset():
        system_status["status"] = "monitoring"
        for i, repo in enumerate(repos):
            repo.update(status="secure", issue="Monitoring active", severity="none")

    threading.Timer(90.0, _auto_reset).start()
    return {"status": "ok"}


# ─── Real public-repo scan (War Room) ────────────────────────────────────────
# No GitHub token required; uses GitHub's public unauthenticated Contents API.
# Rate limited per-IP so a single visitor can't exhaust the upstream quota.

class ScanBody(BaseModel):
    repo: str


@app.post("/api/scan")
def scan_endpoint(body: ScanBody, request: Request):
    ip = _client_ip(request)
    _enforce(f"war_room_scan:{ip}", limit=15, window=60, lockout_secs=60)
    try:
        result = scan_repo(body.repo)
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"ok": False, "error": "SCAN_ERROR",
                     "message": f"Scan failed unexpectedly: {type(e).__name__}"},
        )
    return result


# ─── Production: serve the built frontend ────────────────────────────────────
# In dev, the Vite dev server runs separately and proxies /api → 127.0.0.1:8000.
# In production (autoscale deployment), Vite is not running — this backend is the
# only process. We serve the frontend's `dist/public` build directory and
# fall back to index.html for client-side routes (SPA).
#
# Registered AFTER all /api/* routes so FastAPI's route table takes precedence.

_DIST = (Path(__file__).resolve().parent.parent / "artifacts" / "repoguard" / "dist" / "public").resolve()
_INDEX = _DIST / "index.html"

if _DIST.is_dir() and _INDEX.is_file():
    _ASSETS = _DIST / "assets"
    if _ASSETS.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_ASSETS)), name="assets")

    @app.get("/", include_in_schema=False)
    def _spa_root():
        return FileResponse(str(_INDEX))

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str):
        # /api/* routes are matched first by FastAPI; this only sees non-API paths.
        # Resolve and enforce the path stays inside _DIST to block traversal
        # (`..`, absolute paths, symlink escapes).
        try:
            candidate = (_DIST / full_path).resolve()
            candidate.relative_to(_DIST)
        except (ValueError, OSError):
            # Escapes _DIST → fall back to SPA index, never disclose host files.
            return FileResponse(str(_INDEX))
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_INDEX))
