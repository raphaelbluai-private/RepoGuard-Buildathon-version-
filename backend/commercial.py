"""RepoGuard commercial API support.

Day-1 production adapter around the existing deterministic scanner.
Provides repository HEAD resolution, SQLite-backed result caching, and a stable
machine contract without changing the public /api/scan behavior.
"""

from __future__ import annotations

import copy
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import requests

from scanner import normalize_repo, scan_repo, RULES_EXECUTED

GITHUB_API = "https://api.github.com"
TIMEOUT = 8
SCANNER_VERSION = os.environ.get("REPOGUARD_SCANNER_VERSION", "1.0")
CACHE_TTL_SECONDS = int(os.environ.get("REPOGUARD_CACHE_TTL_SECONDS", "86400"))
CACHE_DB_PATH = os.environ.get(
    "REPOGUARD_CACHE_DB",
    str(Path(__file__).resolve().parent / "repoguard-cache.sqlite3"),
)

_CACHE_LOCK = threading.Lock()


def _github_headers() -> dict[str, str]:
    headers = {
        "User-Agent": "RepoGuard-Commercial/1.0",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = (
        os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
    )
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_auth_configured() -> bool:
    return bool(
        os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
    )


def _connect() -> sqlite3.Connection:
    db_path = Path(CACHE_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_cache (
            cache_key TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            repo TEXT NOT NULL,
            default_branch TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            scanner_version TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            payload TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def cache_key(owner: str, repo: str, default_branch: str, commit_sha: str) -> str:
    return ":".join(
        [owner.lower(), repo.lower(), default_branch, commit_sha, SCANNER_VERSION]
    )


def cache_get(key: str) -> dict[str, Any] | None:
    now = int(time.time())
    with _CACHE_LOCK:
        with _connect() as conn:
            row = conn.execute(
                "SELECT created_at, payload FROM scan_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row:
                return None
            created_at, payload = row
            if now - int(created_at) > CACHE_TTL_SECONDS:
                conn.execute("DELETE FROM scan_cache WHERE cache_key = ?", (key,))
                conn.commit()
                return None
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                conn.execute("DELETE FROM scan_cache WHERE cache_key = ?", (key,))
                conn.commit()
                return None


def cache_put(
    key: str,
    owner: str,
    repo: str,
    default_branch: str,
    commit_sha: str,
    payload: dict[str, Any],
) -> None:
    with _CACHE_LOCK:
        with _connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scan_cache
                (cache_key, owner, repo, default_branch, commit_sha,
                 scanner_version, created_at, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    owner,
                    repo,
                    default_branch,
                    commit_sha,
                    SCANNER_VERSION,
                    int(time.time()),
                    json.dumps(payload, separators=(",", ":")),
                ),
            )
            conn.commit()


def resolve_repo_identity(repo_input: str) -> dict[str, Any]:
    owner, repo, err = normalize_repo(repo_input)
    if err:
        return {"ok": False, "error": "INVALID_INPUT", "message": err}

    headers = _github_headers()
    try:
        meta_r = requests.get(
            f"{GITHUB_API}/repos/{owner}/{repo}", headers=headers, timeout=TIMEOUT
        )
    except requests.RequestException:
        return {
            "ok": False,
            "error": "NETWORK_ERROR",
            "message": "Could not reach GitHub.",
        }

    if meta_r.status_code == 404:
        return {
            "ok": False,
            "error": "REPO_NOT_PUBLIC_OR_INACCESSIBLE",
            "message": f"Repository '{owner}/{repo}' is inaccessible or does not exist.",
        }
    if meta_r.status_code in (403, 429):
        return {
            "ok": False,
            "error": "GITHUB_CAPACITY_ERROR",
            "message": "GitHub refused the repository identity request.",
        }
    if meta_r.status_code != 200:
        return {
            "ok": False,
            "error": "GITHUB_ERROR",
            "message": f"GitHub returned HTTP {meta_r.status_code}.",
        }

    try:
        meta = meta_r.json()
    except ValueError:
        return {"ok": False, "error": "GITHUB_ERROR", "message": "Invalid GitHub response."}

    default_branch = meta.get("default_branch") or "main"
    try:
        head_r = requests.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/commits/{default_branch}",
            headers=headers,
            timeout=TIMEOUT,
        )
    except requests.RequestException:
        return {
            "ok": False,
            "error": "NETWORK_ERROR",
            "message": "Could not resolve repository HEAD.",
        }

    if head_r.status_code in (403, 429):
        return {
            "ok": False,
            "error": "GITHUB_CAPACITY_ERROR",
            "message": "GitHub refused the repository HEAD request.",
        }
    if head_r.status_code != 200:
        return {
            "ok": False,
            "error": "GITHUB_ERROR",
            "message": f"Could not resolve repository HEAD (HTTP {head_r.status_code}).",
        }

    try:
        commit_sha = head_r.json().get("sha")
    except ValueError:
        commit_sha = None
    if not commit_sha:
        return {
            "ok": False,
            "error": "GITHUB_ERROR",
            "message": "GitHub did not return a commit SHA.",
        }

    return {
        "ok": True,
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}",
        "default_branch": default_branch,
        "commit_sha": commit_sha,
    }


def _severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        severity = finding.get("severity")
        if severity in counts:
            counts[severity] += 1
    return counts


def _recommended_action(status: str) -> str:
    return {
        "SAFE_TO_SHIP": "PROCEED_TO_DEPLOYMENT",
        "NEEDS_REVIEW": "REVIEW_FINDINGS_BEFORE_DEPLOYMENT",
        "SHIP_BLOCKED": "REMEDIATE_BEFORE_DEPLOYMENT",
    }.get(status, "REVIEW_SCAN_RESULT")


def to_v1_contract(
    scan_result: dict[str, Any], identity: dict[str, Any], *, cache_hit: bool
) -> dict[str, Any]:
    findings = scan_result.get("findings") or []
    counts = _severity_counts(findings)
    status = scan_result.get("status", "NEEDS_REVIEW")
    return {
        "ok": True,
        "service": "repoguard",
        "version": "1.0",
        "scanner_version": SCANNER_VERSION,
        "repo": identity["full_name"],
        "default_branch": identity["default_branch"],
        "commit": identity["commit_sha"],
        "score": scan_result.get("score"),
        "status": status,
        "rules_executed": scan_result.get("rulesExecuted", RULES_EXECUTED),
        "finding_count": len(findings),
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "findings": findings,
        "gates": scan_result.get("gates") or [],
        "recommended_action": _recommended_action(status),
        "cache_hit": cache_hit,
    }


def commercial_scan(repo_input: str) -> tuple[dict[str, Any], int]:
    identity = resolve_repo_identity(repo_input)
    if not identity.get("ok"):
        return identity, 400 if identity.get("error") == "INVALID_INPUT" else 502

    key = cache_key(
        identity["owner"],
        identity["repo"],
        identity["default_branch"],
        identity["commit_sha"],
    )
    cached = cache_get(key)
    if cached is not None:
        payload = copy.deepcopy(cached)
        payload["cache_hit"] = True
        return payload, 200

    scan_result = scan_repo(repo_input)
    if not scan_result.get("ok"):
        error = scan_result.get("error")
        status = 400 if error == "INVALID_INPUT" else 502
        return scan_result, status

    payload = to_v1_contract(scan_result, identity, cache_hit=False)
    cache_put(
        key,
        identity["owner"],
        identity["repo"],
        identity["default_branch"],
        identity["commit_sha"],
        payload,
    )
    return payload, 200
