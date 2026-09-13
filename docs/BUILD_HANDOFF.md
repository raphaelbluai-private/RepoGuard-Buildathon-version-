# REPO GUARD BUILD HANDOFF

**Governance:** RAPHAEL Master Spec v1.6  
**Mission:** RepoGuard x402 Production Realization + Continuous Completion  
**Canonical repo:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Active branch:** `x402-production`  
**Mission weight:** Critical  

## Current Durable State

Installed into the canonical branch:

- `docs/governance/RAPHAEL_MASTER_SPEC_v1.6_GOVERNANCE.md`
- `docs/governance/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md`
- `docs/REPO_GUARD_CONTINUOUS_COMPLETION_BUILD_TASK.md`
- `.build-state.json`

The existing RepoGuard product foundation remains materially built: deterministic scanner, provider-neutral acquisition, provider adapters, product catalog, x402 middleware/product routes, provenance foundation, telemetry, CI, Docker packaging, and Railway deployment history.

## Current Governance Change

RAPHAEL Master Spec v1.6 now presides over RepoGuard. Historical v1.2/v1.5 mission documents remain evidence/history where useful but may not override v1.6.

The x402 rail is the named ship-path milestone. The build may pursue the earliest narrow production scope that can satisfy v1.6, currently defined as a public-repository-only x402 scanner release. Private-repository/customer credential access remains outside the initial authorized exposure until tenant authorization/isolation is proven.

## Critical Launch-Scope Security Gaps

The following are launch blockers until verified closed for the authorized scope:

1. arbitrary caller-controlled repository URLs must not receive service credentials;
2. SSRF/private/link-local/metadata access must be blocked;
3. private-repository access must remain disabled until tenant authorization/isolation exists;
4. legacy/demo/debug attack surface must be removed or gated;
5. materially equivalent free scan bypass must not undermine paid routes;
6. CORS/public API exposure must be production-scoped;
7. rate/concurrency/request/repository resource controls must be bounded;
8. production container/runtime privilege must be hardened;
9. logs/telemetry/evidence must remain secret-safe;
10. launch-path hostile tests must pass.

## RAPHAEL v1.6 Production Realization Open Work

All applicable domains must receive current release-bound evidence:

1. Source and Traceability
2. Build and Artifact Integrity
3. Security and Supply Chain
4. Environment and Deployment
5. Data and State Continuity
6. Operational Readiness
7. Performance and Reliability
8. Real User Acceptance
9. Production Authorization

Track separately:

- Engineering Green
- Security Green
- Artifact Green
- Deployment Green
- Operations Green
- User Acceptance Green
- Production Authorized

## Exact Next Work Package

**G0 — Canonical State Reconciliation + Continuity Completion**

1. Re-read `.build-state.json` and this handoff.
2. Verify live `x402-production` HEAD.
3. Inspect any commits newer than the recorded checkpoint.
4. Reconstruct the RAPHAEL MASTER TREE from live repository evidence.
5. Create/update requirements traceability, risk register, decision log, interface map, and RED TEAM/failure-mode record at Critical Mission depth.
6. Verify current CI/deployment evidence against the new HEAD; do not inherit old Green automatically.
7. Advance immediately into **G1 — launch-scope security hardening**.

## Critical-Path Freeze

Do not give discretionary refactors, aesthetic changes, speculative provider expansion, low-value edge-case work, or non-launch documentation polish critical-path priority while the x402 ship path can advance.

Exception: a defect or fatal flaw exposed by an executed ship-path/security test immediately becomes critical-path work.

## External / Human Gates

The following may remain BLOCKED/DEFERRED while independent work continues:

- provider credentials/accounts requiring Principal setup;
- external Base Sepolia buyer execution until release candidate is ready;
- Base mainnet transition;
- final Gate 8 production authorization.

Never mark these PASSED without evidence.

## Recovery Rule

The repository carries the build. New agents/operators must recover from the live branch, `.build-state.json`, this handoff, the session recovery protocol, governing docs, current commits, and validation evidence. Do not require prior-chat copy/paste when repository state is sufficient.