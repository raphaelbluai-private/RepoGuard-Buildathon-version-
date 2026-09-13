# RepoGuard x402 Beachhead Sprint 001 — Day 3 Mission Control

**Version:** 0.2  
**Date:** 2026-08-18  
**Status:** ENGINEERING GREEN / DEPLOYMENT + EXTERNAL PURCHASE PENDING  
**Source of Truth:** `x402-production` branch  
**Governing Standard:** RAPHAEL Master Governance & Mission Assurance Protocol v1.2; Appendix A RAPHAEL Master Coding Standard v1.4

## 1. Day 3 Objective

Make RepoGuard discoverable to x402-aware agents, persist machine-commerce transaction evidence, package the validated application for a public HTTPS deployment, and prepare the acceptance path for an external agent purchase before any Base mainnet authorization.

## 2. Discovery Implementation

RepoGuard declares paid `POST /v1/scan` through the x402 v2 Bazaar extension with service name `RepoGuard`, tags (`security`, `github`, `devtools`, `repository`), JSON body schema requiring `repo`, an input example, an output example, and an autonomous-buyer-oriented resource description.

The production application also exposes `GET /.well-known/x402` as a RepoGuard-owned machine-readable bootstrap/fallback manifest. Bazaar remains the canonical x402 discovery mechanism.

## 3. Transaction Telemetry

`backend/commerce_telemetry.py` persists beachhead commerce events without retaining payment signatures or private wallet material. Events include payment challenge, settlement success/failure, scan served, and cache-hit scan. Where available, safe settlement fields include transaction hash, network, payer, and a SHA-256 digest of the payment response.

Public aggregate counters are exposed at `GET /v1/commerce/summary` and in `/v1/health`.

## 4. Deployment Packaging

Validated deployment artifacts:

- root `Dockerfile`: Node 22 workspace frontend build + Python 3.11 runtime
- `.dockerignore`: excludes source-control/runtime state while preserving frontend workspace sources
- `railway.toml`: `/v1/health` deployment healthcheck and restart-on-failure policy
- `backend/.env.production.example`: non-secret production/testnet environment contract

The Docker image installs production Python dependencies from `backend/requirements.txt`, including x402 EVM, FastAPI and extensions extras. The Docker build explicitly copies the workspace `tsconfig.base.json` and `artifacts/` sources required by the real frontend build.

For persistent cache and commerce evidence, the host should mount `/data` and set:

- `REPOGUARD_CACHE_DB=/data/repoguard-cache.sqlite3`
- `REPOGUARD_TELEMETRY_DB=/data/repoguard-commerce.sqlite3`

## 5. CI Evidence

Two Day-3 engineering corrections were intentionally surfaced by CI rather than hidden:

1. Bazaar import initially failed because x402 extensions validation requires its runtime extra. Dependency configuration was corrected to `x402[evm,extensions,fastapi]>=2.20.0,<3`.
2. The first production-container gate exposed missing workspace paths in the Docker context (`artifacts/` and root `tsconfig.base.json`). The Dockerfile/context were corrected and a mandatory container build gate retained.

Current-head GitHub Actions run **`32211144730`** validates:

- frontend typecheck: PASS
- frontend production build: PASS
- backend production modules compile: PASS
- correctness-critical lint: PASS
- scanner/API/x402/discovery/telemetry suite: **56 passed**
- production Docker image build: **PASS**
- Bazaar POST body declaration: PASS
- machine-readable discovery manifest: PASS
- commerce telemetry regression: PASS

**Day-3 engineering classification: GREEN.**

## 6. RED TEAM / Failure Controls

| ID | Failure Mode | Severity | Control | Status |
|---|---|---|---|---|
| D3-FM-001 | Agent cannot infer paid route | High | Bazaar schema + well-known manifest | CONTROLLED IN CODE |
| D3-FM-002 | Settlement lacks transaction evidence | High | final-response telemetry + aggregate counters | LIVE EVIDENCE PENDING |
| D3-FM-003 | Telemetry stores private payment material | Critical | no signature/private-key persistence | CONTROLLED |
| D3-FM-004 | Cache/telemetry lost on restart | High | `/data` persistent-volume contract | HOST VOLUME PENDING |
| D3-FM-005 | Deployment image is not buildable | Critical | mandatory Docker build gate | CONTROLLED |
| D3-FM-006 | Wrong production app entrypoint | Critical | container starts `backend/run.py` -> `commercial_app:app` | CONTROLLED |
| D3-FM-007 | Discovery assumed rather than proven | High | external-agent purchase remains mandatory | ACTIVE HOLD |
| D3-FM-008 | Mainnet before testnet proof | Critical | mainnet interlock | ACTIVE HOLD |

## 7. Remaining Live Acceptance Sequence

1. Connect an authorized deployment host to `x402-production`.
2. Mount persistent `/data` storage.
3. Configure a tightly scoped read-only GitHub credential.
4. Configure the public RepoGuard/AION Base receiver address.
5. Enable x402 on Base Sepolia.
6. Verify `/v1/health`: `github_authenticated=true`, x402 enabled.
7. Verify unpaid `/v1/scan` -> 402.
8. Execute a real Base Sepolia buyer payment.
9. Confirm HTTP 200, settlement evidence, first request `cache_hit=false`.
10. Repeat same repository/SHA purchase; confirm `cache_hit=true`.
11. Verify live commerce telemetry.
12. Verify live x402 discovery.
13. Complete an external-agent discovery purchase.
14. Record acceptance evidence.
15. Only then consider Base mainnet authorization.

## 8. External Inputs / Integrations Still Required

- authorized hosting connection for a public HTTPS service
- public Base-compatible RepoGuard/AION receiving address
- production-host read-only GitHub credential
- buyer wallet funded for Base Sepolia test payment
- later, approved mainnet-capable facilitator configuration/credentials if required

No seed phrase or private key is to be committed to the repository or mission documentation.

## 9. Day 3 Exit Decision

**Discovery engineering:** GREEN  
**Transaction telemetry engineering:** GREEN  
**Production container build:** GREEN  
**Public deployed endpoint:** PENDING AUTHORIZED HOST CONNECTION  
**Authenticated GitHub production access:** PENDING HOST SECRET  
**Real Base Sepolia settlement/cache acceptance:** PENDING EXTERNAL WALLET + HOST  
**External-agent discovery purchase:** PENDING LIVE DEPLOYMENT  
**Base mainnet authorization:** BLOCKED
