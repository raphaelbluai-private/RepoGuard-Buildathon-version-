# REPO GUARD BUILD HANDOFF

**Governance:** RAPHAEL Master Spec v1.6  
**Mission:** RepoGuard x402 Production Realization + Continuous Completion  
**Canonical repo:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Active branch:** `x402-production`  
**Mission weight:** Critical  
**Primary ship path:** hardened public-repository scanner + x402 Base Sepolia acceptance  

## Current Durable State

Installed in the canonical branch:

- `docs/governance/RAPHAEL_MASTER_SPEC_v1.6_GOVERNANCE.md`
- `docs/governance/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md`
- `docs/REPO_GUARD_CONTINUOUS_COMPLETION_BUILD_TASK.md`
- `.build-state.json`
- `docs/BUILD_HANDOFF.md`
- `docs/SESSION_RECOVERY_PROTOCOL.md`
- `docs/mission-assurance/RG-V16-G0-RECONCILIATION.md`
- `docs/RAPHAEL_MASTER_TREE_v1.6.md`

RAPHAEL Master Spec v1.6 presides. Older v1.2/v1.5 documents remain historical evidence only where not superseded.

## G0 Status

**G0 canonical reconciliation: substantially complete.**

Current state is recoverable from the repository without chat-copy dependency. Requirements, risks, decisions, interfaces, RED TEAM cases, Master Tree, build state, handoff, and recovery procedure are now persisted.

The exact latest branch HEAD should always be re-read at recovery time. `.build-state.json` records the last reconciled and validated checkpoints rather than pretending that a state file can name its own future commit.

## Current G1 Security Hardening Progress

The following launch-scope controls are implemented:

1. caller-supplied full clone URLs must use HTTPS;
2. hosted providers are bound to their expected hostnames;
3. embedded URL credentials are rejected;
4. private, loopback, link-local, multicast, reserved, and unspecified destinations are rejected;
5. DNS-resolved destinations are checked before outbound Git operations;
6. Git redirects are disabled for outbound repository acquisition;
7. provider authentication headers are scoped to the intended HTTPS host;
8. self-hosted Gitea/Gogs/OneDev URLs are disabled by default;
9. public-preview mode is enabled by default;
10. providers requiring authentication/private access are blocked from preview scope;
11. optional service-level provider credentials are suppressed during public preview;
12. legacy free scan, demo auth, demo controls, internal diagnostics, and old verifier routes are blocked in the hardened production composition;
13. wildcard browser CORS from the mounted legacy app is stripped at the hardened commerce boundary;
14. request field/body sizes are bounded;
15. concurrent scans are bounded by a fail-closed capacity gate;
16. the production container runs as a non-root `repoguard` user;
17. the hardened launch profile is documented in `.env.production.example`.

## Current Validation Evidence

Validated code checkpoint:

`1fec8733234aa07cdc5da82ebaad5f2a1da8c986`

GitHub Actions run:

`34777506621`

Result:

- backend compile: PASSED
- correctness-critical lint: PASSED
- scanner/API/x402/discovery/telemetry/security regression suite: PASSED
- frontend typecheck: PASSED
- frontend production build: PASSED
- production container build: PASSED

Historical Green does not automatically carry forward to later source/runtime changes; release-candidate validation must be rerun on the final candidate.

## Current Launch Scope

The earliest proposed production authorization remains:

> Public-repository deterministic RepoGuard scanner + x402 paid product rail.

Private/authenticated repository access remains disabled until customer-scoped authorization and tenant isolation are implemented and verified.

## Remaining G1 Work

G1 remains active until launch-scope Security Green is evidenced.

Required remaining work includes:

1. run hostile/adversarial staging cases against SSRF, credential forwarding, URL redirects, malformed input, oversized input, concurrency/resource exhaustion, secret/log redaction, and legacy-route bypass;
2. verify production security headers and deployed CORS behavior;
3. run dependency/container vulnerability review and disposition findings;
4. verify production runtime privilege and resource limits;
5. verify platform/edge abuse protection or record the exact compensating application controls;
6. resolve GitHub branch-protection/release-integrity gap;
7. resolve the public repository / proprietary backend exposure decision;
8. verify current hardened Railway deployment identity and health before moving to G2/G5 acceptance.

## External / Administrative Gates

These may require Principal/admin action and must not be falsely marked complete:

- changing repository visibility or separating proprietary backend source;
- enabling GitHub branch protection / required checks if not available through the current build tool;
- credentials/accounts needed for later authenticated-provider scope;
- Base mainnet transition;
- Gate 8 production authorization.

## Exact Next Work Package

Continue **G1 — Launch-Scope Security Hardening**.

After G1 Security Green:

1. G2 — x402 contract/payment/idempotency reconciliation;
2. G3–G4 — RAPHAEL v1.6 Production Realization evidence;
3. G5 — live Base Sepolia acceptance;
4. G6 — external-agent acceptance;
5. G7 — Gates 1–7 evidence package and Gate 8 presentation;
6. G8 — continue remaining full completion automatically.

## Critical-Path Freeze

No discretionary UI work, feature expansion, provider expansion, style-only refactor, or low-value edge-case accumulation receives critical-path priority while an x402 ship-path milestone can advance.

Any security, correctness, tenant-isolation, payment-integrity, or runtime-identity defect exposed by an executed ship-path test immediately becomes critical-path work.

## Recovery Rule

The repository carries the build. On any new session:

1. read RAPHAEL v1.6 governance;
2. read `.build-state.json`;
3. read this handoff;
4. read `SESSION_RECOVERY_PROTOCOL.md`;
5. read `RAPHAEL_MASTER_TREE_v1.6.md`;
6. inspect live `x402-production` HEAD and newer commits;
7. verify the most recent CI/runtime evidence before inheriting any Green state;
8. resume the exact next package without reopening completed work absent evidence of a gap.
