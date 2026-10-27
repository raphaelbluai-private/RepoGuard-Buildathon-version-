#!/usr/bin/env python3
"""Fail closed on any unapproved Gitleaks finding."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "build" / "release-evidence" / "gitleaks-report.json"
ALLOW = ROOT / "docs" / "security" / "GITLEAKS_TEST_FIXTURE_ALLOWLIST.json"
OUT = ROOT / "build" / "release-evidence" / "repository-secret-history-evidence.json"


def main() -> None:
    findings = json.loads(REPORT.read_text()) if REPORT.exists() and REPORT.stat().st_size else []
    policy = json.loads(ALLOW.read_text())
    allowed = {item["fingerprint"]: item for item in policy["entries"]}
    observed = {item.get("Fingerprint"): item for item in findings}

    unexpected = [
        {
            "fingerprint": item.get("Fingerprint"),
            "rule_id": item.get("RuleID"),
            "file": item.get("File"),
            "commit": item.get("Commit"),
            "line": item.get("StartLine"),
        }
        for item in findings
        if item.get("Fingerprint") not in allowed
    ]
    allowed_observed = [
        {
            "fingerprint": fp,
            "rule_id": observed[fp].get("RuleID"),
            "file": observed[fp].get("File"),
            "commit": observed[fp].get("Commit"),
            "line": observed[fp].get("StartLine"),
            "rationale": allowed[fp]["rationale"],
        }
        for fp in sorted(set(observed) & set(allowed))
    ]
    stale_allowlist = sorted(set(allowed) - set(observed))

    evidence = {
        "schema": "repoguard.repository-secret-history.v1",
        "scanner": "gitleaks 8.21.2",
        "history_scope": "all fetched refs/history",
        "redacted": True,
        "finding_count": len(findings),
        "allowed_fixture_findings": allowed_observed,
        "unexpected_finding_count": len(unexpected),
        "unexpected_findings": unexpected,
        "stale_allowlist_fingerprints": stale_allowlist,
        "status": "PASS" if not unexpected else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    if unexpected:
        print(json.dumps(unexpected, indent=2, sort_keys=True))
        raise SystemExit(f"Unapproved secret-history findings: {len(unexpected)}")
    print(f"Secret-history policy PASS: {len(allowed_observed)} intentional fixture finding(s), 0 unexpected.")


if __name__ == "__main__":
    main()
