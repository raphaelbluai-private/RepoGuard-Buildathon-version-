from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

from source_adapters import adapter_version

SCANNER_VERSION = os.environ.get("REPOGUARD_SCANNER_VERSION", "1.0.0")
RULESET_VERSION = os.environ.get("REPOGUARD_RULESET_VERSION", "1.0.0")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _stable_result_material(result: dict[str, Any]) -> dict[str, Any]:
    material = dict(result)
    material.pop("scanTime", None)
    material.pop("timestamp", None)
    return material


def canonical_result_hash(result: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(_stable_result_material(result))).hexdigest()


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
    try:
        active_adapter_version = adapter_version(provider_key)
    except ValueError:
        active_adapter_version = f"{provider_key}-1.0.0"
    identity = {
        "source_provider": provider_key,
        "repository": repository,
        "repository_url": repository_url,
        "commit_sha": commit_sha,
        "scanner_version": SCANNER_VERSION,
        "ruleset_version": RULESET_VERSION,
        "adapter_version": active_adapter_version,
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


def build_attestation(provenance: dict[str, Any]) -> dict[str, Any]:
    material = {
        "scan_id": provenance.get("scan_id"),
        "source_provider": provenance.get("source_provider"),
        "repository": provenance.get("repository"),
        "commit_sha": provenance.get("commit_sha"),
        "scanner_version": provenance.get("scanner_version"),
        "ruleset_version": provenance.get("ruleset_version"),
        "adapter_version": provenance.get("adapter_version"),
        "result_hash": provenance.get("result_hash"),
        "safe_to_ship": provenance.get("safe_to_ship"),
    }
    digest = hashlib.sha256(_canonical_json(material)).hexdigest()
    return {
        "attestation_id": "rga_" + digest[:24],
        **material,
        "timestamp": provenance.get("timestamp"),
        "attestation_hash": "sha256:" + digest,
    }
