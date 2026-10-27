"""RAPHAEL Security Gates 1-7 evidence evaluation.

This module packages evidence; it never grants Gate 8 authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PASS = "PASS"
PARTIAL = "PARTIAL"
BLOCKED = "BLOCKED"
NOT_APPLICABLE = "NOT_APPLICABLE_FOR_LAUNCH_SCOPE"


@dataclass(frozen=True)
class Control:
    control_id: str
    status: str
    evidence: str
    blocker: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {
            "control_id": self.control_id,
            "status": self.status,
            "evidence": self.evidence,
        }
        if self.blocker:
            data["blocker"] = self.blocker
        return data


def _gate(gate: int, name: str, controls: list[Control]) -> dict[str, Any]:
    statuses = {c.status for c in controls}
    if BLOCKED in statuses:
        status = BLOCKED
    elif PARTIAL in statuses:
        status = PARTIAL
    elif statuses <= {PASS, NOT_APPLICABLE}:
        status = PASS
    else:
        status = PARTIAL
    return {
        "gate": gate,
        "name": name,
        "status": status,
        "controls": [c.as_dict() for c in controls],
    }


def evaluate_gates(*, source_sha: str, ci_run_id: str | None = None) -> dict[str, Any]:
    gates = [
        _gate(1, "Repository Integrity", [
            Control("G1-CI", PASS, "Exact-source-head CI is mandatory and evidence-bound."),
            Control("G1-SECRETS", PASS, "Repository/current-history secret scan runs in CI."),
            Control("G1-BRANCH", BLOCKED, "Fail-closed release-assurance evaluator exists.", "x402-production branch protection and required-check enforcement require repository administration."),
            Control("G1-VISIBILITY", BLOCKED, "Repository visibility is measured by release-assurance evidence.", "Current public-source disposition requires explicit Principal approval or repository visibility change."),
        ]),
        _gate(2, "Application Attack Surface", [
            Control("G2-ROUTES", PASS, "Legacy/demo/internal bypass routes are blocked on the hardened commerce surface."),
            Control("G2-INPUTS", PASS, "Request/body/field bounds and invalid content-length rejection are tested."),
            Control("G2-CORS", PASS, "CORS is closed by default and wildcard origin is rejected."),
            Control("G2-HEADERS", PASS, "HSTS, CSP, no-store, clickjacking, MIME, referrer and permissions headers are regression-tested."),
            Control("G2-ERRORS", PASS, "Security-sensitive scanner/provider failures fail closed without raw secret disclosure."),
        ]),
        _gate(3, "Identity and Tenant Isolation", [
            Control("G3-PUBLIC-SCOPE", PASS, "Public-preview mode is secure-by-default and only public-scan providers are allowed."),
            Control("G3-PRIVATE-ACCESS", NOT_APPLICABLE, "Authenticated/private repository access is excluded and blocked for the limited public-preview launch scope."),
            Control("G3-TENANTS", NOT_APPLICABLE, "The limited public-preview launch has no customer tenant data plane; private multi-tenant access remains deferred."),
        ]),
        _gate(4, "Secrets and Network Boundaries", [
            Control("G4-SSRF", PASS, "HTTPS/provider-host binding, DNS destination validation, and private/metadata address blocking are hostile-tested."),
            Control("G4-CREDENTIALS", PASS, "Embedded credentials are rejected; Git redirects are disabled; auth headers are scoped; public preview suppresses optional credentials."),
            Control("G4-LOGGING", PASS, "Operational alert secret redaction is hostile-tested."),
            Control("G4-EGRESS", BLOCKED, "Application destinations are constrained by provider/network controls.", "Platform-level egress policy must be verified on the deployed Railway candidate."),
        ]),
        _gate(5, "Supply Chain and Runtime", [
            Control("G5-DEPS", PASS, "Locked Python and Node dependency audits run in exact-head CI."),
            Control("G5-CONTAINER", PASS, "Non-root final runtime is rootfs-scanned for fixed HIGH/CRITICAL vulnerabilities."),
            Control("G5-TOOLING", PASS, "pip/setuptools/wheel/ensurepip are removed from the final production runtime."),
            Control("G5-PROVENANCE", PASS, "Exact source SHA and OCI revision are tied to release evidence."),
            Control("G5-DEPLOYED", BLOCKED, "Runtime identity/reconciliation contracts exist.", "Exact Railway deployed artifact identity and infrastructure security review remain live/platform evidence."),
        ]),
        _gate(6, "Abuse and Adversarial Testing", [
            Control("G6-CONCURRENCY", PASS, "Bounded concurrent scan gate fails closed under saturation."),
            Control("G6-HOSTILE", PASS, "Dedicated non-live hostile-staging suite covers SSRF, redirect, credential, size, overload, redaction and replay simulation."),
            Control("G6-EDGE", BLOCKED, "Application controls are proven.", "Edge/WAF/platform abuse policy requires deployment-provider verification."),
            Control("G6-LOAD", BLOCKED, "Performance budgets exist.", "Live load/resource acceptance remains deferred until deployed candidate testing."),
            Control("G6-CIRCUIT", PARTIAL, "Provider requests use bounded timeouts and provider failures fail closed.", "Explicit provider circuit-breaker acceptance evidence is not yet complete."),
        ]),
        _gate(7, "Data / Payment / Recovery", [
            Control("G7-REDACTION", PASS, "Structured operational evidence redacts secret material recursively."),
            Control("G7-PAYMENT-ENGINEERING", PASS, "Payment state machine, replay/idempotency protection, settlement reconciliation semantics and receipt issuance are engineering-tested."),
            Control("G7-PERSISTENCE", PASS, "Cache/payment/telemetry persistence and cross-process restart behavior are engineering-tested."),
            Control("G7-RUNBOOKS", PASS, "Rollback/recovery, operator and incident/credential-rotation runbooks exist."),
            Control("G7-PAYMENT-LIVE", BLOCKED, "Engineering payment controls are current.", "Live Base Sepolia settlement/replay/cache acceptance remains required."),
            Control("G7-RECOVERY-LIVE", BLOCKED, "Persistence contract is proven locally.", "Railway volume restart/redeploy recovery must be verified on the target platform."),
        ]),
    ]
    blockers = [
        {
            "gate": gate["gate"],
            "control_id": control["control_id"],
            "blocker": control.get("blocker"),
        }
        for gate in gates
        for control in gate["controls"]
        if control["status"] in {BLOCKED, PARTIAL} and control.get("blocker")
    ]
    return {
        "schema": "repoguard.raphael-security-gates-1-7.v1",
        "source_commit": source_sha,
        "ci_run_id": ci_run_id,
        "gate8_authorized": False,
        "package_complete": True,
        "all_gates_pass": all(g["status"] == PASS for g in gates),
        "gates": gates,
        "remaining_blockers": blockers,
    }
