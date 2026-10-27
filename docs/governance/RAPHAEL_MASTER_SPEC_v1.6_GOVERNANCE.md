# RAPHAEL MASTER SPEC v1.6 — REPOGUARD GOVERNANCE ADOPTION

**Status:** CONTROLLING GOVERNANCE FOR REPOGUARD  
**Version:** 1.6  
**Mission:** REPO GUARD x402 Production Realization + Continuous Completion  
**Canonical repository:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Canonical branch:** `x402-production`  
**Mission weight:** Critical  
**Decision authority:** Principal / authorized human launch authority

---

## 1. Governing Authority

RAPHAEL Master Spec v1.6 is the presiding governance, mission-assurance, continuity, production-realization, operational-readiness, release-authorization, RED TEAM, and build-execution authority for RepoGuard.

The adopted source document is:

`RAPHAEL_Master_Spec_v1.6_Unified_Governance_Mission_Assurance_Continuity_MasterTree_Production_Realization.docx`

This repository control adopts the full v1.6 specification as controlling law. Earlier RAPHAEL versions, prior chat instructions, historical GREEN claims, prototype behavior, convenience refactors, stale handoffs, screenshots, and unsupported status labels cannot override v1.6.

If two applicable controls conflict, use the stricter control unless the Principal records an explicit governed exception.

---

## 2. Binding Operating Doctrine

- RAPHAEL governs the intelligence.
- RED TEAM independently attacks weakness.
- 30/10 +300% sets the minimum quality and completeness threshold.
- RAPHAEL–NASA Mission Assurance controls readiness.
- WAR ROOM governs disciplined execution.
- The repository carries the build. Conversation does not carry the build.
- Live canonical repository evidence overrides stale summaries or historical status.
- Engineering Green is not Production Authorized.
- Deployment completion is not production evidence.
- The artifact tested must be the artifact shipped.
- Historical Green evidence does not prove current production readiness.
- Missing, stale, expired, blocked, deferred, or not-run evidence may not be represented as PASSED.
- Material launch decisions remain human-authorized.

---

## 3. RepoGuard Mission Objective

Complete and launch RepoGuard's x402 rail as soon as safely possible while driving every required 🟥 item in the current RAPHAEL MASTER TREE to 🟩 through evidence-backed implementation and verification.

The first launch scope may be narrower than the final platform scope if RAPHAEL v1.6 permits a controlled, evidence-backed, human-authorized release. A limited public-repository x402 scanner release may therefore become Production Authorized before every post-launch expansion feature is complete, provided:

1. the authorized scope is explicit;
2. all fatal flaws inside that scope are resolved;
3. Security Green, Artifact Green, Deployment Green, Operations Green, and User Acceptance Green are supported by current evidence;
4. Base/payment acceptance evidence is current;
5. deferred scope is not mislabeled as complete; and
6. Gate 8 launch authorization is recorded by the Principal.

Completion work does not stop after the limited launch. The continuous build proceeds through the remaining required red-status items in dependency order until the governed Master Tree is Green except for formally Not Applicable, Deferred, or externally Blocked items.

---

## 4. Mandatory Continuity Artifacts

Per RAPHAEL v1.6 Section 27, RepoGuard must maintain:

- `.build-state.json`
- `docs/BUILD_HANDOFF.md`
- `docs/SESSION_RECOVERY_PROTOCOL.md`
- a current RAPHAEL MASTER TREE in the required one-block status format
- current governing specifications and approved task/implementation documents

Each meaningful build batch must update the handoff and build-state checkpoint before operational handoff.

---

## 5. Required Master Tree Status Language

Use:

- 🟩 READY — implemented and satisfies the applicable evidence/validation gate.
- 🟨 PARTIALLY COMPLETE — implemented/specifed/materially advanced but not fully validated.
- 🟥 NEEDS BUILDING — required implementation or acceptance work remains materially incomplete.
- 🟪 LEGACY / REMOVE — superseded, duplicate, deprecated, donor-only, or scheduled for removal.
- ⬛ BLOCKED — external condition prevents execution; not an application failure.
- ⏸ DEFERRED — intentionally held by approved sequencing; not a pass.

Code existence alone never earns 🟩.

---

## 6. Production Realization Domains — Mandatory for x402 Launch

RepoGuard must produce current evidence for all applicable RAPHAEL v1.6 Section 28 domains:

### Domain 1 — Source and Traceability
Prove authoritative requirements, decisions, source state, release scope, and exact release baseline.

### Domain 2 — Build and Artifact Integrity
Prove the tested artifact is the shipped artifact; record immutable artifact identity, dependency/build provenance, configuration class, and release manifest.

### Domain 3 — Security and Supply Chain
Prove dependency, vulnerability, secret, credential, permission, runtime, supply-chain, and distribution security. The RAPHAEL Security Governance Protocol applies as a stricter companion control where applicable.

### Domain 4 — Environment and Deployment
Prove target environment, deployment route, deployed identity, authorized configuration, TLS/domain/runtime dependencies, and target-environment smoke/mission verification.

### Domain 5 — Data and State Continuity
Prove persistent state behavior, backup/restore, migration/recovery, rollback or forward-recovery boundaries, and idempotent failure handling where applicable.

### Domain 6 — Operational Readiness
Prove health/readiness/version identity, logs, metrics, alerts, secret-safe telemetry, operator runbook, disablement, restart, recovery, and incident procedures.

### Domain 7 — Performance and Reliability
Define and verify latency, concurrency, timeout, rate-limit, resource, provider-failure, retry, overload, and recovery budgets.

### Domain 8 — Real User Acceptance
Prove an intended external agent/consumer can discover, pay for, invoke, receive, and verify the intended x402 product without undeclared developer intervention.

### Domain 9 — Production Authorization
Record the exact artifact, configuration, environment, evidence set, accepted risks, limitations, scope, authorizing person, and decision time.

---

## 7. Required v1.6 Status Model

Track these separately:

- Engineering Green
- Security Green
- Artifact Green
- Deployment Green
- Operations Green
- User Acceptance Green
- Production Authorized

Allowed evidence/control states:

`PASSED`, `FAILED`, `BLOCKED`, `NOT RUN`, `DEFERRED`, `EXPIRED`, `SUPERSEDED`, `NOT APPLICABLE`, `WAIVED / RISK ACCEPTED`.

Only `PASSED` counts as passed. Risk acceptance never relabels a failed or unexecuted control as passed.

---

## 8. Security Fatal-Flaw Rule

For the public x402 scanner launch, the following are launch-blocking until resolved or removed from the authorized exposure:

- service-level credentials can be forwarded to caller-controlled hosts;
- SSRF can reach loopback, private, link-local, metadata, or other forbidden networks;
- private-repository access can cross customer/tenant authorization boundaries;
- production secrets appear in source, logs, telemetry, reports, screenshots, or evidence;
- legacy/demo/debug endpoints expose materially unsafe production behavior;
- x402 payment can be bypassed for materially equivalent paid capability;
- idempotent payment/retry behavior can double-charge or double-execute unsafely;
- production runtime identity cannot be tied to the approved artifact/configuration;
- critical/high practical vulnerabilities remain unresolved inside launch scope.

---

## 9. Critical-Path Rule

RepoGuard is revenue-adjacent and x402 launch is the named ship-path milestone.

No discretionary hardening, styling, refactor, edge-case expansion, CI policy refinement, recovery micro-test, documentation embellishment, provider expansion, or non-launch feature may take critical-path priority while a named x402 ship-path milestone can advance.

**Exception:** a defect or fatal flaw exposed by an executed ship-path/security test immediately enters the critical path.

Security fatal flaws are not discretionary hardening.

---

## 10. External-Gate Rule

A credential, wallet, provider account, external marketplace, live network, production-domain, or other external dependency may be marked `BLOCKED` or `DEFERRED` without stopping unrelated build work.

When an external gate is unavailable:

- continue architecture, security, code, tests, fixtures, static review, evidence structure, continuity, and other independent work;
- never infer a pass;
- record exact owner and next action;
- resume the gate immediately when the dependency becomes available.

---

## 11. Verification / Release Rule

Before RepoGuard can be declared v1.6-verified for the authorized x402 launch scope, the exact release candidate must satisfy:

1. current requirements traceability;
2. RED TEAM review and fatal-flaw disposition;
3. security verification under the RAPHAEL Security Governance Protocol;
4. full CI/regression on the release commit;
5. release artifact identity and provenance;
6. deployed artifact/configuration identity reconciliation;
7. target-environment post-deployment verification;
8. persistent state / telemetry / recovery verification where applicable;
9. Base Sepolia payment challenge, settlement, fulfillment, repeat/cache, and retrieval evidence;
10. external autonomous-agent discovery/purchase evidence for the intended launch path;
11. current evidence freshness ledger;
12. operator runbook and incident/disablement path;
13. RAPHAEL Gates 1–7 passed or formally dispositioned without false PASS labels; and
14. Gate 8 Principal launch authorization.

---

## 12. Enforcement

This file is binding on RepoGuard build execution until superseded by a later Principal-authorized RAPHAEL version.

No agent, developer, chat, CI pipeline, deployment platform, or prior summary may self-authorize production.

All RepoGuard continuous-completion work must reference this governance control and RAPHAEL Master Spec v1.6.