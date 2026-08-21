from __future__ import annotations

from typing import Any

_PROVIDER_CAPABILITIES = {
    "github": {"status": "active", "adapter_version": "github-1.0.0"},
    "gitlab": {"status": "planned"},
    "bitbucket": {"status": "planned"},
    "azure_devops": {"status": "planned"},
    "gitea": {"status": "planned"},
    "codeberg": {"status": "planned"},
    "aws_codecommit": {"status": "planned"},
    "sourcehut": {"status": "planned"},
    "onedev": {"status": "planned"},
    "sourceforge": {"status": "planned"},
}


def provider_capabilities() -> dict[str, dict[str, Any]]:
    return {k: dict(v) for k, v in _PROVIDER_CAPABILITIES.items()}


def safe_to_ship_view(result: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    findings = result.get("findings") or []
    blocking = sum(1 for f in findings if f.get("severity") in {"critical", "high"})
    return {
        "scan_id": provenance.get("scan_id"),
        "commit_sha": provenance.get("commit_sha"),
        "result_hash": provenance.get("result_hash"),
        "safe_to_ship": result.get("status") == "SAFE_TO_SHIP",
        "status": result.get("status"),
        "score": result.get("score"),
        "blocking_findings": blocking,
    }


def remediation_view(result: dict[str, Any], scan_id: str) -> dict[str, Any]:
    remediation = []
    for finding in result.get("findings") or []:
        fix_plan = finding.get("fixPlan") or []
        remediation.append({
            "finding_id": finding.get("id"),
            "rule_id": finding.get("ruleId"),
            "severity": finding.get("severity"),
            "problem": finding.get("shortExplanation"),
            "recommended_action": finding.get("howToFix"),
            "steps": fix_plan,
            "verification": fix_plan[-1] if fix_plan else "Re-run RepoGuard and confirm the finding is cleared.",
        })
    return {"scan_id": scan_id, "remediation": remediation}
