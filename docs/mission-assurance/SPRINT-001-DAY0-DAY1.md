# RepoGuard x402 Beachhead Sprint 001 — Day 0 / Day 1 Mission Control

**Version:** 0.1  
**Date:** 2026-08-18  
**Status:** ACTIVE — YELLOW / PROCEED WITH CONTROLS  
**Source of Truth:** `x402-production` branch of this repository  
**Governing Standard:** RAPHAEL Master Governance & Mission Assurance Protocol v1.2; Appendix A RAPHAEL Master Coding Standard v1.4

## 1. Mission Charter / Mission Card

- **Mission Name:** RepoGuard x402 Beachhead Sprint 001
- **Mission Weight:** Heavy
- **Mission Type:** software product build + paid public-facing offer
- **Mission Objective:** Convert the existing deterministic RepoGuard scanner into a production-hardened, versioned machine API ready to receive x402 payments without redesigning the scanner.
- **Strategic Reason:** Establish RepoGuard as AION's first machine-commerce capability and obtain the first external autonomous USDC payment.
- **Owner / Decision Authority:** AION principal
- **Engineering Source of Truth:** GitHub repository, `x402-production` branch until launch authorization
- **Immediate Exit Target for Day 1:** scanner regression suite, stable `/v1/scan`, authenticated GitHub capability, commit-SHA cache, controlled error contract, scanner-protecting CI, real frontend build in CI.
- **Kill / Pause Trigger:** deterministic scanner regression, unstable response contract, unbounded GitHub request behavior, security regression, or inability to prove repeatable fixture outcomes.

## 2. Day 0 Baseline Findings

| Control | Baseline | Day 0/1 disposition |
|---|---|---|
| Existing deterministic scanner | Present | Preserve; no rewrite |
| Existing public endpoint `/api/scan` | Present | Preserve for UI/backward compatibility |
| CI protects default branch | Failed | Corrected on `x402-production` workflow |
| CI syntax-checks scanner | Failed | Corrected |
| Frontend actually builds in CI | Failed | Corrected |
| Scanner regression fixtures | Missing | Added deterministic regression suite |
| Versioned commercial endpoint | Missing | Added `/v1/scan` via production composition app |
| GitHub authenticated access capability | Already coded in scanner | Production health exposes configuration state; production host must supply read-only token |
| Commit-SHA cache | Missing | Added SQLite cache keyed by owner/repo/default branch/commit/scanner version |
| Release regression gate | Missing | Added |
| x402 payment boundary | Not yet implemented | Day 2; launch blocked until completed |

## 3. Assumptions Register

| ID | Assumption | Confidence | Impact if wrong | Validation | Status |
|---|---|---:|---:|---|---|
| A-001 | Existing scanner rules are deterministic for identical fetched repository state | High | High | regression repeatability tests | VALIDATING |
| A-002 | Existing scanner result is commercially useful without an LLM | High | High | Day 1 contract + external paid use | OPEN |
| A-003 | A read-only GitHub credential is sufficient for public-repo launch capacity | Medium | High | production token + load telemetry | OPEN |
| A-004 | SQLite is sufficient for beachhead cache volume | Medium | Medium | cache hit/latency telemetry | OPEN |
| A-005 | Stable commit SHA is a valid cache invalidation boundary | High | High | same-SHA hit / new-SHA miss tests | VALIDATING |
| A-006 | $0.01/$0.05/$0.25 pricing can be supported economically | Low | Medium | Day 3-5 transaction telemetry | OPEN |

## 4. Requirements Traceability Matrix

| ID | Requirement | Risk controlled | Validation method | Evidence |
|---|---|---|---|---|
| REQ-001 | Existing `/api/scan` remains available | compatibility | API regression | `backend/app.py` unchanged |
| REQ-002 | Add stable `POST /v1/scan` | machine contract drift | TestClient schema assertions | `backend/commercial_app.py`, tests |
| REQ-003 | Response includes repo, commit, score, status, rule count, finding counts, findings and recommendation | buyer usability | contract tests | `test_commercial_api.py` |
| REQ-004 | Same repo/branch/SHA/scanner version uses cache | GitHub capacity | same-SHA test | SQLite cache tests |
| REQ-005 | New commit SHA invalidates result cache | stale evidence | new-SHA test | API cache tests |
| REQ-006 | GitHub credential is sent when configured | upstream quota | auth-header test | commercial unit tests |
| REQ-007 | Scanner fixtures cover clean and known-bad cases | false confidence | deterministic rule tests | scanner regression suite |
| REQ-008 | CI compiles scanner and production API modules | release regression | GitHub Actions | `.github/workflows/ci.yml` |
| REQ-009 | CI builds and typechecks frontend | deployment regression | GitHub Actions | `.github/workflows/ci.yml` |
| REQ-010 | Release workflow reruns regression suite | bad tagged release | GitHub Actions | `.github/workflows/release.yml` |

## 5. RED TEAM / Failure Modes

| ID | Failure Mode | Severity | Prevention / Control | Kill criterion |
|---|---|---|---|---|
| FM-001 | Scanner behavior changes silently | High | deterministic regression suite | any unexplained fixture drift |
| FM-002 | Cache serves stale repository state | High | commit-SHA cache key | observed same key for different HEAD |
| FM-003 | Anonymous GitHub quota throttles paid scans | High | authenticated token + cache | sustained upstream capacity errors |
| FM-004 | Commercial endpoint leaks demo behavior into contract | Medium | separate production composition app | contract becomes non-versioned/unstable |
| FM-005 | Rate limiter can be bypassed via spoofed forwarding header | Medium | existing socket-IP behavior retained | confirmed bypass |
| FM-006 | Runtime cache becomes committed state | Medium | `.gitignore` SQLite patterns | cache DB appears in release/source |
| FM-007 | Tests pass but production app is not the app deployed | High | deployment command must target `commercial_app:app` | host points only to legacy app at commercial launch |
| FM-008 | Mainnet payments are enabled before payment-path verification | Critical | Day 2 testnet gate | any request to bypass testnet gate |

## 6. Interface Control Map

| Interface | Sends | Receives | Failure risk | Control |
|---|---|---|---|---|
| Agent → `/v1/scan` | repo identifier | stable JSON result | malformed input / abuse | Pydantic + rate limiter |
| Commercial adapter → GitHub | repository metadata + HEAD request | branch + commit SHA | quota / upstream error | token + bounded timeout + explicit errors |
| Commercial adapter → Scanner | repo identifier | deterministic scanner result | scanner regression | preserved scanner + regression suite |
| Commercial adapter → SQLite | cache key + payload | cached payload | stale/corrupt cache | SHA/version key + TTL + invalid JSON eviction |
| GitHub Actions → build/test | source tree | pass/fail evidence | false release confidence | scanner tests + frontend build |

## 7. Decision Log

| Date | Decision | Class | Reason | Risk accepted |
|---|---|---|---|---|
| 2026-08-18 | Preserve `demo`; create `x402-production` working branch | C | minimal controlled change, preserves buildathon history | temporary branch structure |
| 2026-08-18 | Do not rewrite scanner | C | core capability already exists | inherited scanner limitations |
| 2026-08-18 | Add production API as composition layer | C | avoids destabilizing current UI app | production host must use correct app target |
| 2026-08-18 | Use SQLite for Sprint 001 cache | C | avoids Redis dependency before revenue | single-node cache limitation |
| 2026-08-18 | Hold x402 implementation until Day 0/1 regression gate is green | A/C | payment cannot precede validated product boundary | schedule pressure |

## 8. Day 1 Launch Gate

Day 1 is **not Green** until GitHub Actions evidence proves all of the following:

- scanner modules compile
- scanner regression tests pass
- clean fixture resolves SAFE_TO_SHIP
- committed `.env` fixture resolves SHIP_BLOCKED
- `permissions: write-all` fixture resolves SHIP_BLOCKED
- missing build script is detected
- `curl | sh` is detected
- score/status repeatability is proven
- `/v1/scan` response contract is stable
- same-SHA request returns cache hit
- changed SHA forces rescan
- rate limiter rejects request 31 in the test window
- frontend typecheck passes
- frontend production build passes

## 9. Day 1 Remaining External Dependency

Before launch, production hosting must set one tightly scoped read-only GitHub credential using one of:

- `GITHUB_PERSONAL_ACCESS_TOKEN`
- `GITHUB_TOKEN`
- `GH_TOKEN`

`GET /v1/health` reports whether authenticated GitHub access is configured. No credential value is returned.

## 10. Day 2 Hold Point

x402, wallet configuration, facilitator/CDP credentials and Base Sepolia payment enforcement are explicitly outside Day 0/1. They may begin only after the Day 1 CI gate is green.
