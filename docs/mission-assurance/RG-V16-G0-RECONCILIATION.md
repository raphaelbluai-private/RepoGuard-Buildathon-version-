# REPO GUARD — RAPHAEL v1.6 G0 CANONICAL STATE RECONCILIATION

**Task:** `RG-V16-CONTINUOUS-COMPLETION-001`  
**Mission Weight:** Critical  
**Canonical Repository:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Canonical Branch:** `x402-production`  
**Governing Authority:** RAPHAEL Master Spec v1.6  
**Ship Path:** Hardened public-repository scanner + x402 Base Sepolia acceptance, then controlled launch authorization  

## 1. Canonical State

The repository is the build source of truth. Historical chat claims and prior GREEN labels do not override live repository evidence.

Baseline implementation checkpoint for this reconciliation batch:

- branch: `x402-production`
- implementation head before this reconciliation document: `1fec8733234aa07cdc5da82ebaad5f2a1da8c986`
- production repository visibility: public at time of review
- branch protection: not enabled at time of review
- release commits observed as unsigned at time of review
- RAPHAEL v1.6 governance: installed
- RAPHAEL Security Governance Protocol: installed
- continuous completion task: installed

The final HEAD after continuity artifacts are updated is recorded in `.build-state.json` and `docs/BUILD_HANDOFF.md`.

## 2. Approved Initial Launch Scope

The earliest launch scope is intentionally limited to:

> Public-repository deterministic RepoGuard scanning and x402 paid product access on Base Sepolia, with private/authenticated repository access disabled until tenant/customer authorization and isolation are verified.

This scope exists to move the x402 rail forward without accepting unnecessary private-data risk.

## 3. Requirements Traceability

| ID | Requirement | Risk Controlled | Implementation / Evidence | Current Status |
|---|---|---|---|---|
| RG-V16-001 | RAPHAEL v1.6 presides | stale governance | `docs/governance/RAPHAEL_MASTER_SPEC_v1.6_GOVERNANCE.md` | VERIFIED |
| RG-V16-002 | Security protocol installed | inconsistent hardening | `docs/governance/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md` | VERIFIED |
| RG-V16-003 | Continuous completion task persists ship path | cross-session drift | `docs/REPO_GUARD_CONTINUOUS_COMPLETION_BUILD_TASK.md` | VERIFIED |
| RG-V16-004 | Public preview defaults to public repositories only | unauthorized private repo access | `launch_security.py`, `commerce_app_v2.py` | IMPLEMENTED / CI EVIDENCE CURRENT FOR LATEST TESTED HEAD |
| RG-V16-005 | Optional provider credentials suppressed during preview | shared credential/private repo exposure | `source_adapters._auth_header` | IMPLEMENTED / TESTED |
| RG-V16-006 | Caller cannot redirect provider credential to arbitrary host | credential exfiltration | provider/host binding + host-scoped Git header | IMPLEMENTED / TESTED |
| RG-V16-007 | SSRF private/internal destinations blocked | internal network/cloud metadata access | HTTPS-only, provider-host validation, IP filtering, redirect disablement | IMPLEMENTED / TESTED; hostile staging still required |
| RG-V16-008 | Legacy/demo commercial bypass blocked | unpaid scan / demo attack surface | parent commerce middleware returns 410 | IMPLEMENTED / TESTED |
| RG-V16-009 | Wildcard browser CORS removed from hardened production surface | cross-origin browser abuse | hardened response CORS filter | IMPLEMENTED / TESTED |
| RG-V16-010 | Oversized request rejected | resource exhaustion | 64 KiB default declared-body cap | IMPLEMENTED / TESTED THROUGH APP REGRESSION SURFACE |
| RG-V16-011 | Concurrent scans bounded | process exhaustion | `ScanConcurrencyGate`, default 4 | IMPLEMENTED / TESTED |
| RG-V16-012 | Runtime container non-root | container privilege | Docker `USER repoguard` | IMPLEMENTED / CONTAINER BUILD EVIDENCE REQUIRED ON CURRENT HEAD |
| RG-V16-013 | x402 product pricing remains canonical | stale single-price bypass | `product_catalog.py` | VERIFIED IN TEST SUITE |
| RG-V16-014 | Base mainnet remains human-gated | premature real-money exposure | mainnet hold + continuous task | VERIFIED IN GOVERNANCE; runtime revalidation required before mainnet |
| RG-V16-015 | Live Sepolia settlement proven on hardened release | payment-path acceptance | G5 | NOT RUN |
| RG-V16-016 | External agent completes autonomous purchase | user acceptance | G6 | NOT RUN |
| RG-V16-017 | Release branch protection enabled | unauthorized release mutation | GitHub branch settings | BLOCKED / HUMAN OR ADMIN-CONFIG ACTION REQUIRED |
| RG-V16-018 | Proprietary production backend exposure dispositioned | IP/source exposure | repository visibility/separation decision | OPEN / Principal decision required |

## 4. Risk Register

| Risk | Severity | Current Control | Status / Next Action |
|---|---:|---|---|
| Credential forwarding to attacker-controlled host | Critical | hosted-provider allowlist, host-scoped auth header, redirects disabled | CONTROLLED IN CODE; hostile verification pending |
| SSRF to localhost/private/link-local/metadata network | Critical | URL + DNS/IP destination checks | CONTROLLED IN CODE; hostile staging pending |
| Shared optional token enables private repo access in preview | Critical | optional auth suppressed when preview-only | CONTROLLED IN CODE |
| Private tenant A data accessed by tenant B | Critical | private/authenticated launch providers disabled | CONTAINED BY LAUNCH SCOPE; full tenant model deferred |
| Free legacy scan bypasses x402 | Critical | `/api/scan` blocked by hardened parent app | CONTROLLED IN PRODUCTION COMPOSITION |
| Demo auth/control endpoints exposed | High | hardened parent app blocks known demo/internal routes | CONTROLLED IN PRODUCTION COMPOSITION |
| Wildcard browser CORS | High | outer commerce layer strips wildcard CORS; allowlist opt-in | CONTROLLED IN PRODUCTION COMPOSITION |
| Resource exhaustion by many scans | High | request-size cap, Git timeouts, file-size cap, bounded concurrency | PARTIALLY CONTROLLED; live load/edge evidence pending |
| Container compromise has root privileges | High | non-root `repoguard` runtime user | IMPLEMENTED; current-head image build/runtime evidence pending |
| Public repository exposes proprietary backend | High / IP | none technical while repository remains public | OPEN / launch governance decision required |
| Production branch mutation bypasses reviewed release | High | CI exists but branch is unprotected | OPEN / branch protection required |
| Railway deploys branch commits before final acceptance | High | CI exists; deployment source known | OPEN / release process must be reconciled under G3/G4 |
| Payment retry/double fulfillment | Critical | x402 middleware + tests | G2/G5 idempotency evidence still required |
| Mainnet enabled before testnet proof | Critical | explicit governance hold | CONTROLLED |

## 5. Decision Log

1. **Preserve deterministic scanner core.** No scanner rewrite without root-cause evidence.
2. **Launch public repositories first.** Private repository access is outside initial launch scope.
3. **Default preview mode is secure-on.** `REPOGUARD_PUBLIC_PREVIEW_ONLY=1` unless deliberately disabled after later authorization work.
4. **Self-hosted provider URLs are disabled by default.** They require an explicit environment override after trust-boundary review.
5. **Hosted providers are bound to known hosts.** Full URLs cannot point a provider credential at an arbitrary domain.
6. **Git redirects are disabled on credential-bearing acquisition.** Redirect-based credential forwarding is not accepted.
7. **Legacy/demo routes remain in source for compatibility but are blocked in the hardened production composition.** Removal is later legacy cleanup unless tests expose a bypass.
8. **Container runs non-root.** Root runtime is not accepted for the public launch candidate.
9. **Base mainnet remains human-gated.** No agent may self-authorize real-money launch.
10. **Security defects exposed by ship-path testing outrank discretionary work.** Otherwise ship-path milestones remain priority.

## 6. Interface Control Map

| Interface | Trust Boundary | Control |
|---|---|---|
| Public agent → RepoGuard API | hostile Internet input | Pydantic bounds, body cap, legacy route block, x402 paid boundary |
| RepoGuard → Git provider | outbound SSRF/credential boundary | HTTPS, provider host binding, DNS/IP validation, redirect disablement, host-scoped auth |
| RepoGuard → temporary clone | untrusted repository contents | shallow/no-checkout clone, temporary directory, file selection, 1 MiB per extracted file, timeouts |
| RepoGuard → scanner | untrusted text → deterministic engine | no LLM authority, deterministic rules |
| RepoGuard → cache | repository state reuse | provider/repo/SHA identity; TTL |
| RepoGuard → commerce telemetry | transaction evidence | no raw payment signatures/private keys; bounded safe metadata |
| Buyer → x402 middleware | economic/authenticity boundary | payment challenge and verification before protected route fulfillment |
| GitHub → CI | release evidence | compile, lint, regression suite, frontend build, production container gate |
| GitHub branch → Railway | deployment boundary | current direct branch deployment; must be reconciled with release authorization in G3/G4 |

## 7. RED TEAM / Failure Modes

| ID | Failure Mode | Severity | Required Result |
|---|---|---:|---|
| RT-001 | `provider=gitlab` + attacker URL receives GitLab token | Critical | BLOCKED |
| RT-002 | caller uses `http://` clone URL | High | BLOCKED |
| RT-003 | caller targets localhost/private/link-local/metadata endpoint | Critical | BLOCKED |
| RT-004 | self-hosted provider URL used in public launch without explicit approval | High | BLOCKED |
| RT-005 | optional GitHub token accesses private repo during preview | Critical | TOKEN NOT ATTACHED |
| RT-006 | legacy `/api/scan` provides free equivalent scan | Critical | HTTP 410 on hardened service |
| RT-007 | demo auth/trigger route reachable through hardened service | High | HTTP 410 |
| RT-008 | attacker origin receives wildcard CORS | High | NO WILDCARD CORS |
| RT-009 | excessive request body accepted | High | HTTP 413 |
| RT-010 | scan flood exceeds configured process concurrency | High | FAIL CLOSED / 503 |
| RT-011 | container executes as root | High | NON-ROOT |
| RT-012 | payment retry double-charges/double-fulfills | Critical | MUST FAIL SAFE; G2/G5 proof required |
| RT-013 | deployed artifact cannot be tied to authorized source | Critical | LAUNCH BLOCKED |
| RT-014 | external agent needs undocumented human intervention to buy | High | G6 FAIL until autonomous path succeeds |

## 8. Evidence Ledger

Evidence is recorded as current only for the exact source state it validates.

Known evidence in this hardening sequence:

- intentional RED CI demonstrated missing SSRF/credential controls before implementation;
- SSRF/provider host/credential-scoping tests added and later passed after implementation;
- public-preview credential suppression was introduced test-first;
- wildcard CORS regression was introduced test-first;
- concurrency-capacity regression was introduced test-first;
- frontend build and backend compile/lint/regression gates are active;
- production container gate exists and must pass on the final release candidate before Artifact Green.

The live final CI run, Railway deployment identity, hostile staging evidence, Sepolia payment evidence, and external-agent acceptance must be appended or referenced by later G1–G7 packages.

## 9. G0 Exit Assessment

G0 is substantially established when this reconciliation record, the Master Tree, `.build-state.json`, `BUILD_HANDOFF.md`, and `SESSION_RECOVERY_PROTOCOL.md` agree on:

- canonical repo/branch;
- current governance;
- current launch scope;
- implemented controls;
- open risks;
- evidence status;
- next package.

The next active work package remains **G1 — Launch-Scope Security Hardening** until hostile staging and all practical launch-blocking security findings for the limited public-repository x402 scope are Green or explicitly blocked by an external/human gate.
