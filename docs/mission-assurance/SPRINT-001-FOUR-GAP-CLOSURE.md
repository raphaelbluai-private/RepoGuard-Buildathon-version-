# RepoGuard x402 Beachhead Sprint 001 — Four-Gap Closure Control

**Version:** 0.3  
**Date:** 2026-08-18  
**Mission:** RepoGuard x402 Beachhead Sprint 001  
**Source of Truth:** `x402-production` until launch authorization  
**Governing Standard:** RAPHAEL Master Governance & Mission Assurance Protocol v1.2

## Purpose

This control prevents the sprint from declaring production readiness while any of the four original production gaps remains unresolved. A gap is CLOSED only when both engineering controls and required operational evidence are present.

## Four-Gap Closure Matrix

| Gap | Original failure | Engineering control now present | Evidence | Residual external/launch work | Closure status |
|---|---|---|---|---|---|
| G-001 CI / default-branch mismatch | CI only targeted `main`/`master` while repository default was `demo`, allowing relevant branches to bypass the intended build gate | CI now triggers on `demo`, `x402-production`, `main`, and `master`; production modules compile; frontend typechecks/builds; regression suite runs | GitHub Actions run `32210848666`: backend and frontend PASS | `demo` remains the GitHub default intentionally while `x402-production` is the controlled sprint source of truth. Final branch/default-branch cutover is a launch-authorization action | **ENGINEERING CLOSED / LAUNCH CUTOVER PENDING** |
| G-002 No scanner regression gate | Deterministic scanner had no meaningful automated regression protection | Scanner, commercial API, payment, bypass, discovery, telemetry and cache tests are blocking in CI; release workflow reruns the same classes of controls | Run `32210848666`: **56 tests passed** plus frontend build | Keep the gate mandatory through launch | **CLOSED** |
| G-003 GitHub API capacity | Anonymous GitHub requests and repeated full rescans could exhaust upstream capacity before paid traffic scales | Auth-aware GitHub headers; HEAD/commit resolution; commit-SHA + scanner-version cache; TTL; cached repeat scan avoids full scanner fanout; explicit 403/429 capacity error contract | Auth-header, same-SHA cache-hit and changed-SHA rescan regressions pass | Public deployment must receive a tightly scoped read-only GitHub credential; `/v1/health` must report `github_authenticated=true`; live traffic must not exhibit unresolved 403/429 capacity failures | **CONTROLLED IN CODE / OPERATIONAL CLOSURE PENDING** |
| G-004 Machine-commerce plumbing | No paid route, payment enforcement, settlement proof, discovery surface or transaction evidence; post-audit also found free `/api/scan` bypass | x402 v2 protects `POST /v1/scan`; legacy bypass blocked when commerce enabled; Base Sepolia `$0.01` exact payment; mainnet interlock; Bazaar discovery declaration; RepoGuard well-known manifest; persistent transaction telemetry; live buyer probe; deployable container | Run `32210848666`: 56 tests, unpaid/invalid payment controls, bypass regression, Bazaar declaration, machine-readable discovery, telemetry round trip | Deploy public HTTPS service; configure receiver + GitHub secret; execute real Base Sepolia settlement and cached repeat; verify live telemetry and discovery; complete external-agent purchase | **ENGINEERING SUBSTANTIALLY CLOSED / LIVE ACCEPTANCE OPEN** |

## Closure Rules

### G-001 is fully closed when
1. Every branch allowed to serve or release RepoGuard is covered by CI.
2. Production deployment uses the validated application composition (`commercial_app:app`).
3. At launch authorization, the canonical branch/default-branch decision is recorded and the deployment source matches it.

### G-002 is fully closed when
1. Scanner fixture regressions are blocking in CI.
2. Release workflow reruns the regression suite.
3. No scanner/payment/discovery behavior change may merge without passing the gate.

### G-003 is fully closed when
1. Production host reports `github_authenticated=true` from `/v1/health`.
2. Same repository SHA produces a cache hit rather than another full scan.
3. A changed SHA produces a rescan.
4. Initial live traffic does not show unresolved 403/429 capacity failures.

### G-004 is fully closed when
1. Unpaid deployed request to `/v1/scan` returns an x402 402 challenge.
2. No alternate public route exposes equivalent full-scan capability for free while commerce is enabled.
3. Real Base Sepolia buyer payment settles and returns a valid scan.
4. Second paid request for the same SHA returns `cache_hit=true`.
5. Settlement/transaction evidence is recorded in telemetry.
6. The paid resource is discoverable through the intended x402 discovery path.
7. An external agent discovers and purchases the resource without a human supplying an undocumented endpoint.
8. Only after all testnet acceptance evidence is recorded may Base mainnet be explicitly authorized.

## Post-Audit Finding: Monetization Bypass

The Day-2 review found a material monetization defect: the production composition preserved legacy `POST /api/scan` as a public, free scanner while only `POST /v1/scan` was x402-protected. That allowed materially equivalent scanner capability without payment.

Remediation on `x402-production`:

- when `REPOGUARD_X402_ENABLED` is false, legacy `/api/scan` remains available for demo/development compatibility;
- when `REPOGUARD_X402_ENABLED` is true, `POST /api/scan` returns HTTP 410 with `COMMERCIAL_ROUTE_REQUIRED` and points to `/v1/scan`;
- regression coverage enforces the boundary.

## Day 3 Closure Work

Day 3 added the remaining machine-commerce engineering controls that were absent from the original build:

- x402 Bazaar discovery extension for the POST JSON resource;
- service name/tags and request/response discovery schema;
- RepoGuard-owned `/.well-known/x402` bootstrap manifest;
- persistent machine-commerce telemetry for payment challenge, settlement result, scan service and cache hits;
- public aggregate commerce counters;
- production Dockerfile and Railway health configuration;
- environment contract for GitHub capacity token, persistent cache/telemetry paths and Base Sepolia x402 settings.

The first Day-3 CI attempt correctly failed because Bazaar validation requires the x402 `extensions` extra. Dependency configuration was corrected to `x402[evm,extensions,fastapi]>=2.20.0,<3`; rerun `32210848666` then passed all 56 tests. The failure and correction are retained as mission evidence rather than hidden.

## Sprint Exit Rule

RepoGuard must **not** be described as production-certified or as having met the x402 beachhead exit criterion until G-001 through G-004 are all CLOSED.

Current classification:

- **G-001:** engineering closed; launch branch cutover pending
- **G-002:** closed
- **G-003:** controlled in code; production credential/traffic evidence pending
- **G-004:** engineering substantially closed; public deployment, real Sepolia settlement/cache proof, live discovery and external-agent purchase pending
- **Overall:** **YELLOW — PROCEED WITH CONTROLS; NOT YET PRODUCTION-CERTIFIED**
