# RepoGuard Operator Runbook

## Scope

This runbook governs the hardened public-repository RepoGuard commerce service on the `x402-production` release path. It does not authorize Base mainnet, private-repository access, or Gate 8 production launch.

## Start / health

1. Confirm the release candidate passed the exact-head CI workflow.
2. Confirm the generated release manifest source commit equals the intended deployment commit.
3. Confirm the production container carries OCI label `org.opencontainers.image.revision` equal to that commit.
4. Configure persistent `/data` storage for cache, commerce telemetry, and payment ledgers.
5. Configure runtime identity variables. For authorized deployment, set `REPOGUARD_REQUIRE_RUNTIME_IDENTITY=1`.
6. Verify `/v1/health` reports `status=ok`, the expected source commit, a configuration hash, and `identity_complete=true`.
7. Internal operators may query `/v1/repoguard/runtime-identity` only with `REPOGUARD_INTERNAL=1`.

## Stop conditions

Immediately stop new paid traffic or place the service in a non-paying maintenance state if any of these occur:

- runtime source commit is unknown or differs from the authorized release manifest;
- payment transaction enters ambiguous settlement state and cannot be reconciled;
- persistent `/data` is unavailable or read-only;
- repeated `SCAN_CAPACITY_EXHAUSTED` alerts indicate sustained saturation;
- provider acquisition shows SSRF/credential-boundary regression;
- dependency/container security gate fails on the candidate;
- payment replay or idempotency controls fail;
- production identity cannot be established.

## Payment incident handling

For `SETTLEMENT_PENDING` with unknown outcome:

1. Do not request or accept a second payment for the same idempotency key.
2. Freeze facilitator identity for the transaction.
3. Preserve transaction ID, request hash, SKU, network, timestamps, and any settlement transaction hash.
4. Reconcile with the original facilitator/payment rail.
5. Only after a definitive result may the transaction advance to `SETTLED`, a terminal failure, or an operator-authorized remediation path.

## Scanner failure after verification

A paid scanner failure must remain a failed fulfillment. Do not convert a scanner error into a successful product response. Retry only when the transaction state is explicitly retriable and payment outcome is unambiguous.

## Capacity

Application concurrency is bounded by `REPOGUARD_MAX_CONCURRENT_SCANS`. Capacity exhaustion returns 503 with retry guidance and emits a structured operational alert. Platform/edge rate limiting remains a separate launch gate.

## Evidence to retain

For every release candidate retain:

- exact Git commit;
- release manifest;
- dependency inventories;
- container image inspection/ID evidence;
- CI run ID/result;
- relevant test count;
- runtime identity/configuration hash;
- deployment ID when available;
- rollback target;
- live acceptance evidence once permitted.

## Escalation

Security, payment-integrity, runtime-identity, or persistence failures are release blockers. They are not downgraded to warnings for schedule convenience.
