# RepoGuard x402 Beachhead Sprint 001 — Four-Gap Closure Control

**Version:** 0.2  
**Date:** 2026-08-18  
**Mission:** RepoGuard x402 Beachhead Sprint 001  
**Source of Truth:** `x402-production` until launch authorization  
**Governing Standard:** RAPHAEL Master Governance & Mission Assurance Protocol v1.2

## Purpose

This control prevents the sprint from declaring production readiness while any of the four original production gaps remains unresolved. A gap is CLOSED only when both engineering controls and required operational evidence are present.

## Four-Gap Closure Matrix

| Gap | Original failure | Engineering control now present | Evidence | Residual external/launch work | Closure status |
|---|---|---|---|---|---|
| G-001 CI / default-branch mismatch | CI only targeted `main`/`master` while repository default was `demo`, allowing relevant branches to bypass the intended build gate | CI now triggers on `demo`, `x402-production`, `main`, and `master`; scanner modules compile; frontend typechecks/builds; regression suite runs | GitHub Actions run `32209865721`: backend and frontend PASS | `demo` remains the GitHub default intentionally while `x402-production` is the controlled sprint source of truth. Final branch/default-branch cutover is a launch-authorization action, not an unprotected-CI state | **ENGINEERING CLOSED / LAUNCH CUTOVER PENDING** |
| G-002 No scanner regression gate | Deterministic scanner had no meaningful automated regression protection, so rule behavior could change silently | Deterministic fixture suite plus commercial API and x402 tests are mandatory in CI and release workflows | Run `32209865721`: **52 tests passed** before the post-audit bypass control; current head must remain green with the added regression | None for beachhead release beyond keeping the gate required | **CLOSED, CURRENT-HEAD CI RECONFIRMATION REQUIRED** |
| G-003 GitHub API capacity | Anonymous GitHub requests and repeated full rescans could exhaust upstream capacity before paid traffic scales | Auth-aware GitHub headers; HEAD/commit resolution; commit-SHA + scanner-version cache; TTL; cached repeat scan avoids full scanner fanout; explicit 403/429 capacity error contract | Auth-header tests, same-SHA cache-hit test, new-SHA rescan test pass in CI | Production host must receive a tightly scoped read-only GitHub credential. Capacity/load telemetry must confirm the beachhead assumptions under real traffic | **CONTROLLED IN CODE / OPERATIONAL CLOSURE PENDING** |
| G-004 Machine-commerce plumbing | No paid machine route, x402 enforcement, wallet settlement proof, discovery surface, or transaction evidence. Post-audit also identified `/api/scan` as a free equivalent-path bypass when x402 was enabled | x402 v2 middleware protects `POST /v1/scan`; Base Sepolia default; `$0.01` exact payment; fail-closed wallet/network config; mainnet release interlock; live buyer probe; production composition now returns `410 COMMERCIAL_ROUTE_REQUIRED` for `POST /api/scan` whenever x402 is enabled | Run `32209865721`: unpaid `/v1/scan` -> 402; invalid payment denied; mainnet premature activation denied. New regression asserts legacy `/api/scan` cannot bypass payment when commerce is enabled | Must deploy public HTTPS endpoint, configure receiver, execute real Base Sepolia paid scan + cached repeat paid scan, confirm settlement evidence; Day 3 must add agent discovery/registration and transaction telemetry before the sprint exit criterion is met | **PARTIALLY CLOSED — FREE BYPASS CONTROLLED; LIVE SETTLEMENT + DISCOVERY/TELEMETRY OPEN** |

## Closure Rules

### G-001 is fully closed when
1. Every branch allowed to serve or release RepoGuard is covered by CI.
2. Production deployment uses the same validated application composition (`commercial_app:app`).
3. At launch authorization, the canonical branch/default-branch decision is recorded and the deployment source matches it.

### G-002 is fully closed when
1. Scanner fixture regressions are blocking in CI.
2. Release workflow reruns the same regression suite.
3. No scanner behavior change may merge without passing the gate.

### G-003 is fully closed when
1. Production host reports `github_authenticated=true` from `/v1/health`.
2. Same repository SHA produces a cache hit rather than another full scan.
3. A changed SHA produces a rescan.
4. Initial live traffic does not show unresolved 403/429 capacity failures.

### G-004 is fully closed when
1. Unpaid production/test endpoint request to `/v1/scan` returns x402 402 challenge.
2. No alternate public route exposes an equivalent full scan without payment when commerce is enabled.
3. Real Base Sepolia buyer payment settles and returns a valid scan.
4. Second paid request for the same SHA returns `cache_hit=true`.
5. Settlement/transaction evidence is recorded in telemetry.
6. An external agent can discover the service and its paid route without a human supplying an undocumented endpoint.
7. Only after the testnet gate passes may Base mainnet be explicitly authorized.

## Post-Audit Finding: Monetization Bypass

The Day-2 review found a material monetization defect: the production composition preserved legacy `POST /api/scan` as a public, free scanner while only `POST /v1/scan` was x402-protected. That meant a buyer or agent could obtain materially equivalent scanner capability without using the paid route.

Remediation applied on `x402-production`:

- when `REPOGUARD_X402_ENABLED` is false, legacy `/api/scan` remains available for demo/development compatibility;
- when `REPOGUARD_X402_ENABLED` is true, `POST /api/scan` returns HTTP 410 with `COMMERCIAL_ROUTE_REQUIRED` and points callers to `/v1/scan`;
- a regression test now enforces this behavior.

This control is required before calling G-004 payment enforcement meaningful.

## Sprint Exit Rule

RepoGuard must **not** be described as production-certified or as having met the x402 beachhead exit criterion until G-001 through G-004 are all CLOSED.

Current classification:

- **G-001:** engineering closed; launch branch cutover pending
- **G-002:** closed, subject to current-head CI remaining green
- **G-003:** controlled in code; production credential/traffic evidence pending
- **G-004:** free bypass controlled; live testnet settlement, discovery, and transaction telemetry pending
- **Overall:** **YELLOW — PROCEED WITH CONTROLS; NOT YET PRODUCTION-CERTIFIED**
