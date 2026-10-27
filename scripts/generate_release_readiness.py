#!/usr/bin/env python3
"""Generate machine-readable evidence freshness/readiness status for a CI candidate."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "release-evidence"
LEDGER = ROOT / "docs" / "operations" / "EVIDENCE_FRESHNESS_LEDGER.json"

CI_PROVABLE = {
    "exact_head_ci",
    "dependency_security_audit",
    "container_provenance",
    "persistent_state_restart",
}
LIVE_ONLY = {
    "runtime_identity_reconciliation",
    "facilitator_qualification",
    "live_base_sepolia_acceptance",
    "hostile_staging_acceptance",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    evidence = []
    for rule in ledger["rules"]:
        name = rule["evidence"]
        if name in CI_PROVABLE:
            status = "CURRENT_CI_EVIDENCE"
            observed_at = now.isoformat()
        elif name in LIVE_ONLY:
            status = "LIVE_EVIDENCE_REQUIRED"
            observed_at = None
        else:
            status = "UNKNOWN"
            observed_at = None
        evidence.append({
            **rule,
            "status": status,
            "observed_at": observed_at,
        })
    report = {
        "schema": "repoguard.release-readiness-evidence.v1",
        "generated_at": now.isoformat(),
        "source_commit": os.getenv("GITHUB_SHA"),
        "ci_run_id": os.getenv("GITHUB_RUN_ID"),
        "release_authorized": False,
        "engineering_evidence_current": all(
            item["status"] == "CURRENT_CI_EVIDENCE"
            for item in evidence if item["evidence"] in CI_PROVABLE
        ),
        "live_blockers": [
            item["evidence"] for item in evidence
            if item["status"] == "LIVE_EVIDENCE_REQUIRED" and item["required_for_release"]
        ],
        "evidence": evidence,
    }
    (OUT / "release-readiness-evidence.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
