# RepoGuard x402 Beachhead Sprint 001 — Day 2 Mission Control

**Version:** 0.1  
**Date:** 2026-08-18  
**Status:** ENGINEERING GREEN / LIVE TESTNET PAYMENT PENDING  
**Source of Truth:** `x402-production` branch  
**Governing Standard:** RAPHAEL Master Governance & Mission Assurance Protocol v1.2; Appendix A RAPHAEL Master Coding Standard v1.4

## 1. Day 2 Objective

Protect `POST /v1/scan` with x402 v2 on Base Sepolia at a launch price of `$0.01`, prove that unpaid and invalid-payment calls are denied, then execute a real testnet payment and confirm a paid scan response before any mainnet transition.

## 2. Implemented Payment Boundary

- x402 protocol version: v2 SDK family
- Python package: `x402[evm,fastapi]>=2.20.0,<3`
- Framework: FastAPI / ASGI middleware
- Protected route: `POST /v1/scan`
- Scheme: `exact`
- Default network: Base Sepolia `eip155:84532`
- Default price: `$0.01`
- Default test facilitator: `https://x402.org/facilitator`
- Default asset behavior: network-default USDC for dollar-denominated price
- Existing `/api/scan` remains outside the x402 commercial boundary for legacy/UI compatibility during Sprint 001.

## 3. Production Configuration

x402 is disabled unless explicitly enabled.  When enabled, configuration is fail-closed.

Required:

- `REPOGUARD_X402_ENABLED=1`
- `REPOGUARD_X402_PAY_TO=<Base-compatible 0x receiver address>`

Day-2 defaults:

- `REPOGUARD_X402_NETWORK=eip155:84532`
- `REPOGUARD_X402_PRICE=$0.01`
- `REPOGUARD_X402_FACILITATOR_URL=https://x402.org/facilitator`

Mainnet is deliberately blocked unless all of the following are true:

- Base Sepolia paid acceptance test has passed
- `REPOGUARD_X402_NETWORK=eip155:8453`
- `REPOGUARD_X402_ALLOW_MAINNET=1`
- a mainnet-capable facilitator is configured
- the testnet-only `x402.org` facilitator is no longer selected

## 4. Day 2 Verification Evidence

GitHub Actions run `32209865721` validated the Day-2 engineering boundary.

- backend production modules compiled: PASS
- correctness-critical lint: PASS
- x402 EVM runtime extras installed: PASS
- scanner/API/x402 suite: **52 passed**
- no-payment request to enabled `/v1/scan`: **402 Payment Required**
- `PAYMENT-REQUIRED` header present: PASS
- invalid `PAYMENT-SIGNATURE`: denied / no 200 response
- invalid receiver wallet configuration: process configuration rejected
- premature Base mainnet selection: rejected unless explicit mainnet release flag is present
- frontend typecheck/build: PASS

## 5. RED TEAM / Failure Controls

| ID | Failure Mode | Severity | Control |
|---|---|---|---|
| D2-FM-001 | Paid route accidentally launches unprotected | Critical | explicit middleware regression proves no-payment returns 402 |
| D2-FM-002 | Invalid payment reaches scanner | Critical | invalid signature regression must not return 200 |
| D2-FM-003 | Wrong receiver address | Critical | strict EVM address validation; enabled app fails closed |
| D2-FM-004 | Mainnet activated before testnet proof | Critical | explicit `REPOGUARD_X402_ALLOW_MAINNET=1` gate |
| D2-FM-005 | Testnet facilitator used on mainnet | Critical | mainnet configuration rejects x402.org facilitator |
| D2-FM-006 | Payment work destabilizes scanner | High | scanner regression suite remains in same CI gate |
| D2-FM-007 | Buyer pays twice but scan recomputes same SHA | Medium | live probe requires second paid call to report `cache_hit=true` |

## 6. Live Testnet Acceptance Gate

Engineering is Green, but Day 2 is not fully accepted until a real Base Sepolia buyer payment is executed.

Acceptance sequence:

1. Deploy `x402-production` with x402 enabled.
2. Configure a real Base-compatible receiver address.
3. Fund a temporary buyer wallet with Base Sepolia test USDC (and any required testnet gas).
4. Verify an unpaid request returns 402.
5. Execute a real paid request using `backend/scripts/x402_testnet_probe.py`.
6. Confirm first paid response returns HTTP 200 and `cache_hit=false`.
7. Execute the same paid request again against the same repository SHA.
8. Confirm second paid response returns HTTP 200 and `cache_hit=true`.
9. Confirm payment settlement evidence is present in the response.
10. Record the acceptance evidence before authorizing Base mainnet.

## 7. External Inputs Still Required

To complete the real-money-equivalent Day-2 testnet gate, the engineering team still requires:

- public receiving wallet address for RepoGuard/AION machine commerce
- a deployed testnet endpoint/host with the Day-2 environment variables
- a temporary buyer wallet funded with Base Sepolia test USDC
- production CDP credentials are not required for the x402.org Base Sepolia test path, but will be required/recommended for the mainnet facilitator transition

## 8. Day 2 Exit Decision

**Engineering boundary:** GREEN  
**No-payment enforcement:** GREEN  
**Invalid-payment enforcement:** GREEN  
**Real Base Sepolia settlement:** PENDING EXTERNAL WALLET/HOST INPUT  
**Mainnet authorization:** BLOCKED
