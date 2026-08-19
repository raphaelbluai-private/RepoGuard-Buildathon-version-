# RepoGuard x402 Beachhead Sprint 001 — Day 3 Mission Control

**Version:** 0.1  
**Date:** 2026-08-18  
**Status:** ENGINEERING GREEN / DEPLOYMENT + EXTERNAL PURCHASE PENDING  
**Source of Truth:** `x402-production` branch  
**Governing Standard:** RAPHAEL Master Governance & Mission Assurance Protocol v1.2; Appendix A RAPHAEL Master Coding Standard v1.4

## 1. Day 3 Objective

Make RepoGuard discoverable to x402-aware agents, persist machine-commerce transaction evidence, package the validated application for a public HTTPS deployment, and prepare the acceptance path for an external agent purchase before any Base mainnet authorization.

## 2. Discovery Implementation

RepoGuard now declares the paid `POST /v1/scan` resource through the x402 v2 Bazaar extension.

Discovery declaration includes:

- service name: `RepoGuard`
- tags: `security`, `github`, `devtools`, `repository`
- HTTP body type: JSON
- required input: `repo`
- example input: `owner/repository`
- response example with commit, score, status, finding count and cache state
- paid route description suitable for autonomous buyers

The production application also exposes `GET /.well-known/x402` as a RepoGuard-owned machine-readable bootstrap/fallback manifest. Bazaar remains the canonical x402 discovery mechanism.

## 3. Transaction Telemetry

`backend/commerce_telemetry.py` provides beachhead-level persistent telemetry without retaining payment signatures or private wallet material.

Recorded events:

- payment challenge issued
- payment settlement success
- payment settlement failure
- scan served
- scan served from cache

When a settlement response is present, telemetry records safely decoded transaction hash, network and payer when available plus a SHA-256 digest of the payment response.

Public aggregate telemetry is available at `GET /v1/commerce/summary`. `/v1/health` also exposes aggregate commerce counters.

## 4. Deployment Packaging

Deployment artifacts added:

- root `Dockerfile`: Node 22 frontend build + Python 3.11 runtime
- `.dockerignore`: excludes source-control/runtime state
- `railway.toml`: healthcheck `/v1/health`, restart-on-failure policy
- `backend/.env.production.example`: production/testnet environment contract without secrets

The container intentionally installs from `backend/requirements.txt`, including x402 EVM, FastAPI and extension dependencies.

For persistent cache and commerce evidence, the deployment host should mount persistent storage at `/data` and configure:

- `REPOGUARD_CACHE_DB=/data/repoguard-cache.sqlite3`
- `REPOGUARD_TELEMETRY_DB=/data/repoguard-commerce.sqlite3`

## 5. CI Evidence

GitHub Actions run `32210848666` validated the Day-3 software boundary after the Bazaar runtime dependency correction:

- frontend typecheck: PASS
- frontend production build: PASS
- production modules compile: PASS
- correctness-critical lint: PASS
- scanner/API/x402/discovery/telemetry suite: **56 passed**
- Bazaar POST body declaration regression: PASS
- machine-readable well-known discovery manifest regression: PASS
- commerce telemetry round-trip regression: PASS

**Day-3 engineering classification: GREEN.**

## 6. RED TEAM / Failure Controls

| ID | Failure Mode | Severity | Control | Status |
|---|---|---|---|---|
| D3-FM-001 | Agent cannot infer how to call paid route | High | Bazaar body schema + RepoGuard well-known manifest | CONTROLLED IN CODE |
| D3-FM-002 | Settlement occurs without transaction evidence | High | final-response telemetry middleware + aggregate counters | CONTROLLED IN CODE; LIVE EVIDENCE PENDING |
| D3-FM-003 | Telemetry stores buyer payment signature/private material | Critical | payment signature never persisted; payment-response digest only | CONTROLLED |
| D3-FM-004 | Deployment loses cache/telemetry on restart | High | `/data` persistent-volume paths documented | HOST VOLUME PENDING |
| D3-FM-005 | Deployment uses wrong application entrypoint | Critical | Docker runtime executes `backend/run.py` -> `commercial_app:app` | CONTROLLED |
| D3-FM-006 | Agent discovery is assumed rather than proven | High | external-agent purchase remains mandatory acceptance evidence | ACTIVE HOLD |
| D3-FM-007 | Mainnet activated before external testnet proof | Critical | existing mainnet interlock remains active | ACTIVE HOLD |

## 7. Deployment / Acceptance Sequence

The remaining sequence is strictly ordered:

1. Connect an authorized deployment host to `x402-production`.
2. Mount persistent storage for `/data`.
3. Configure a tightly scoped read-only GitHub credential.
4. Configure the public RepoGuard receiver address.
5. Enable x402 on Base Sepolia.
6. Verify `/v1/health` returns `github_authenticated=true` and x402 enabled.
7. Verify an unpaid `/v1/scan` call returns 402.
8. Execute a real Base Sepolia buyer payment.
9. Confirm HTTP 200, settlement evidence, and first request `cache_hit=false`.
10. Execute the same repository/SHA purchase again and confirm `cache_hit=true`.
11. Verify transaction counters/evidence in telemetry.
12. Verify the resource is discoverable through the intended x402 discovery path.
13. Complete an external-agent purchase using discovery rather than an undocumented endpoint.
14. Record acceptance evidence.
15. Only then consider Base mainnet authorization.

## 8. External Inputs / Integrations Still Required

The repository cannot manufacture external infrastructure or wallet authority. Before the live gate can execute, the mission requires:

- an authorized hosting connection for the public HTTPS service
- a public Base-compatible RepoGuard/AION receiving address
- a production-host read-only GitHub credential
- a buyer wallet funded for Base Sepolia test payment
- for the later Base mainnet transition, an approved mainnet-capable facilitator configuration and any required facilitator credentials

No seed phrase or private key should be committed to the repository or pasted into mission documentation.

## 9. Day 3 Exit Decision

**Discovery engineering:** GREEN  
**Transaction telemetry engineering:** GREEN  
**Deployment packaging:** GREEN  
**Public deployed endpoint:** PENDING AUTHORIZED HOST CONNECTION  
**Authenticated GitHub production access:** PENDING HOST SECRET  
**Real Base Sepolia settlement/cache acceptance:** PENDING EXTERNAL WALLET + HOST  
**External-agent discovery purchase:** PENDING LIVE DEPLOYMENT  
**Base mainnet authorization:** BLOCKED
