"""Operational readiness checks for RepoGuard release candidates.

This module reports evidence and blockers. It never grants launch authorization.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from runtime_identity import runtime_identity

_DB_ENV = {
    "cache": "REPOGUARD_CACHE_DB",
    "telemetry": "REPOGUARD_TELEMETRY_DB",
    "payments": "REPOGUARD_PAYMENT_DB",
}


def _db_path(name: str, env_key: str) -> dict[str, Any]:
    raw = os.getenv(env_key)
    path = Path(raw).expanduser() if raw else None
    parent = path.parent if path else None
    return {
        "name": name,
        "configured": bool(raw),
        "absolute": bool(path and path.is_absolute()),
        "parent_exists": bool(parent and parent.exists()),
        "parent_writable": bool(parent and os.access(parent, os.W_OK)),
        "path": str(path) if path else None,
    }


def operational_readiness() -> dict[str, Any]:
    identity = runtime_identity()
    persistence = [_db_path(name, key) for name, key in _DB_ENV.items()]
    identity_required = os.getenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "0").strip().lower() in {
        "1", "true", "yes", "on"
    }
    identity_ok = identity.identity_complete if identity_required else True
    persistence_ok = all(
        item["configured"] and item["absolute"] and item["parent_exists"] and item["parent_writable"]
        for item in persistence
    )
    blockers: list[str] = []
    if not identity_ok:
        blockers.append("runtime_identity_incomplete")
    if not persistence_ok:
        blockers.append("persistent_state_not_ready")

    return {
        "schema": "repoguard.operational-readiness.v1",
        "status": "ENGINEERING_READY" if not blockers else "BLOCKED",
        "release_authorized": False,
        "runtime_identity": {
            "required": identity_required,
            "complete": identity.identity_complete,
            "source_commit": identity.source_commit,
            "config_hash": identity.config_hash,
        },
        "persistence": persistence,
        "blockers": blockers,
        "live_evidence_required": [
            "railway_deployment_identity_reconciliation",
            "railway_volume_restart_redeploy_test",
            "runtime_resource_limit_verification",
            "live_alert_delivery",
            "live_performance_load_results",
            "platform_edge_abuse_controls",
            "base_sepolia_acceptance",
            "external_agent_purchase",
            "gate_8_authorization",
        ],
    }
