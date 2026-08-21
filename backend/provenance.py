from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

SCANNER_VERSION = os.environ.get("REPOGUARD_SCANNER_VERSION", "1.0.0")
RULESET_VERSION = os.environ.get("REPOGUARD_RULESET_VERSION", "1.0.0")
ADAPTER_VERSIONS = {
    "github": os.environ.get("REPOGUARD_GITHUB_ADAPTER_VERSION", "github-1.0.0"),
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def canonical_result_hash(result: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(result)).hexdigest()


def build_provenance(
    *,
    provider: str,
    repository: str,
    repository_url: str,
    commit_sha: str | None,
    result: dict[str, Any],
    timestamp: str | None = None,
) -> dict[str, Any]:
    provider_key = provider.lower()
    ts = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result_hash = canonical_result_hash(result)
    identity = {
        "source_provider": provider_key,
        "repository": repository,
        "repository_url": repository_url,
        "commit_sha": commit_sha,
        "scanner_version": SCANNER_VERSION,
        "ruleset_version": RULESET_VERSION,
        "adapter_version": ADAPTER_VERSIONS.get(provider_key, f"{provider_key}-1.0.0"),
        "result_hash": result_hash,
    }
    scan_id = "rg_" + hashlib.sha256(_canonical_json(identity)).hexdigest()[:24]
    status = result.get("status") if isinstance(result, dict) else None
    return {
        "scan_id": scan_id,
        **identity,
        "timestamp": ts,
        "safe_to_ship": status == "SAFE_TO_SHIP",
    }
