# RG-G2 — Payment Operations Assurance

**Canonical repo:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Canonical branch:** `x402-production`  
**Mission:** Add an operations-grade control plane around the existing x402 payment rail without redesigning the deterministic scanner.

## Scope implemented

### Transaction state machine

Durable SQLite-backed transaction and transition records now model:

- `CHALLENGED`
- `PRESENTED`
- `VERIFIED`
- `FULFILLMENT_STARTED`
- `FULFILLED`
- `SETTLEMENT_PENDING`
- `SETTLED`
- `RECEIPT_ISSUED`
- `VERIFICATION_REJECTED`
- `FULFILLMENT_FAILED_RETRIABLE`
- `FULFILLMENT_FAILED_TERMINAL`
- `SETTLEMENT_FAILED_RETRIABLE`
- `SETTLEMENT_FAILED_TERMINAL`
- `REPLAY_REJECTED`
- `IDEMPOTENCY_CONFLICT`
- `EXPIRED`

Every transaction binds request hash, idempotency key, safe payment-proof digest, SKU, price, network, facilitator identity, state history, retryability, transaction hash when available, cache status, response payload, and receipt ID. Raw payment signatures and credentials are not persisted.

### Payment fairness correction

Paid scanner errors no longer return as successful fulfillment payloads. A scanner/runtime failure produces an explicit non-2xx response and records retriable or terminal fulfillment failure. This prevents a failed scanner result from being represented as a successfully fulfilled paid product.

### Idempotency and replay controls

The outer payment-operations boundary executes before x402 payment processing.

- completed idempotent retries return the stored original result without presenting another payment;
- an idempotency key cannot be rebound to another SKU/request hash;
- concurrent duplicate fulfillment is blocked;
- fulfilled-but-unreconciled transactions block another payment and require reconciliation;
- reused payment proofs under another transaction are rejected;
- transaction and receipt IDs are returned as safe response headers.

### x402 lifecycle integration

The x402 resource server lifecycle hooks are bound to the payment ledger:

- after verify -> `VERIFIED`
- verification failure -> `VERIFICATION_REJECTED`
- before settle -> `SETTLEMENT_PENDING`
- after settle -> `SETTLED` then `RECEIPT_ISSUED`
- settle failure -> retriable failure unless the outcome is indeterminate
- settle timeout -> remains `SETTLEMENT_PENDING`; operator reconciliation is required before another payment

The endpoint handler remains responsible for `FULFILLMENT_STARTED`, `FULFILLED`, and fulfillment failures.

### Payment telemetry

Metrics are derived from immutable transaction/transition evidence rather than current-state snapshots:

- challenge rate
- payment success rate
- settlement failure rate
- fulfillment failure rate
- verify p50/p95 latency
- fulfillment p50/p95 latency
- settlement p50/p95 latency
- total p50/p95 latency
- unique SKU volume
- unique settled revenue by SKU
- replay attempts
- cache-assisted fulfillment rate

Retries do not create additional settled revenue counts.

### Facilitator qualification contract

RepoGuard now codifies:

- Base Sepolia and Base as the approved network family;
- public `x402.org` facilitator as testnet-only for RepoGuard;
- x402 SDK version pinned to `2.22.0`;
- HTTPS-only facilitator URL;
- no automatic facilitator switch after a payment has been presented;
- settlement timeout as an indeterminate state requiring reconciliation;
- deterministic behavior for verify/settle timeout, 5xx, malformed response, and network-unavailable classes.

## CI contract

G2 tests include:

- happy path through receipt issuance;
- idempotent request identity;
- idempotency conflict;
- payment-proof replay rejection;
- invalid state transition fail-closed behavior;
- settlement-timeout preservation;
- unique revenue/SKU accounting;
- cache-assisted fulfillment;
- scanner failure after payment;
- network/price transaction binding;
- facilitator testnet/mainnet policy;
- failover freeze after payment presentation;
- verify/settle timeout, 5xx, malformed response, and network failure semantics.

## Evidence still required before production authorization

The following cannot be marked verified from code/tests alone:

- measured facilitator availability/error rate under RepoGuard traffic;
- authoritative facilitator rate and volume limits;
- live Base Sepolia settlement against the hardened release candidate;
- live settlement-timeout/reconciliation drill;
- persistent-state restart recovery;
- same-request live idempotency and replay acceptance test;
- external autonomous-agent purchase;
- Base mainnet facilitator qualification;
- Principal Gate 8 authorization.

## Failover rule

Before payment presentation, RepoGuard may select another qualified facilitator.

After payment presentation, facilitator identity is frozen for the transaction. A verification, settlement, network, or timeout failure is reconciled against that facilitator/payment before a new payment is accepted. Automatic post-presentation failover is prohibited because it can create ambiguous or duplicate settlement.

## Status

**Engineering:** YELLOW pending exact-head CI.  
**Live payment operations:** RED pending Base Sepolia and facilitator evidence.  
**Mainnet:** BLOCKED pending live acceptance and Principal authorization.
