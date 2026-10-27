from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scanner import (
    CORE_FILES,
    RULES_EXECUTED,
    SEVERITY_WEIGHTS,
    _calc_score,
    _derive_gates,
    _derive_status,
    _run_checks,
)
from source_adapters import fetch_snapshot, normalize_provider_key


def scan_repo_provider(provider: str, repo_input: str) -> dict[str, Any]:
    key = normalize_provider_key(provider)
    snapshot = fetch_snapshot(key, repo_input, CORE_FILES)
    if not snapshot.get("ok"):
        return snapshot

    file_map = snapshot.get("file_map") or {}
    findings, signals = _run_checks(file_map)
    for finding in findings:
        finding["source"] = f"live_{key}_scan"

    score = _calc_score(findings)
    status = _derive_status(score, findings)
    gates = _derive_gates(signals, findings)
    repo_id = snapshot.get("repository_id") or repo_input
    parts = [p for p in str(repo_id).split("/") if p]
    owner = "/".join(parts[:-1]) if len(parts) > 1 else None
    name = parts[-1] if parts else str(repo_id)

    return {
        "ok": True,
        "provider": key,
        "repo": {
            "provider": key,
            "owner": owner,
            "name": name,
            "fullName": repo_id,
            "url": snapshot.get("repository_url"),
            "defaultBranch": snapshot.get("default_branch"),
            "stars": None,
            "language": None,
            "description": None,
        },
        "commitSha": snapshot.get("commit_sha"),
        "commitTimestamp": snapshot.get("commit_timestamp"),
        "scanTime": datetime.now(timezone.utc).isoformat(),
        "filesScanned": list(file_map.keys()),
        "filesUnavailable": max(0, len(CORE_FILES) - len(file_map)),
        "rulesExecuted": RULES_EXECUTED,
        "findings": findings,
        "score": score,
        "scoreProjected": min(100, score + sum(
            SEVERITY_WEIGHTS.get(f.get("severity"), 0) for f in findings
        )),
        "status": status,
        "gates": gates,
        "snapshot": {
            "provider": key,
            "repository_id": repo_id,
            "repository_url": snapshot.get("repository_url"),
            "default_branch": snapshot.get("default_branch"),
            "commit_sha": snapshot.get("commit_sha"),
            "commit_timestamp": snapshot.get("commit_timestamp"),
            "visibility": snapshot.get("visibility"),
            "adapter_version": (snapshot.get("metadata") or {}).get("adapter_version"),
            "files": [
                {k: f.get(k) for k in ("path", "size", "content_hash")}
                for f in snapshot.get("files") or []
            ],
        },
    }
