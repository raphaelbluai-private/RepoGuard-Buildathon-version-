# RepoGuard Incident, Credential Rotation, Rollback & Recovery Runbook

## Credential rotation

RepoGuard must never log raw provider tokens, payment signatures, private keys, passwords, or wallet secrets.

When a credential is suspected or confirmed compromised:

1. revoke/rotate it at the issuing provider first;
2. update the platform secret store;
3. redeploy from the same authorized source commit unless a code change is required;
4. confirm runtime identity and configuration hash after redeploy;
5. run the applicable provider/payment smoke gate;
6. document the incident and evidence without copying the secret into tickets, logs, or chat.

## Rollback decision

Rollback when the current deployment has a release-regression that cannot be safely corrected in-place without exposing customers to payment, security, or availability risk.

The rollback target must be the most recent release candidate that has:

- exact-head CI Green;
- known source commit;
- known container provenance;
- compatible persistence schema;
- no superseding critical security defect.

## Rollback procedure

1. Stop or drain new paid requests if payment state may be ambiguous.
2. Snapshot/retain the persistent `/data` volume before changing versions.
3. Record current source commit, deployment ID, image identity, and config hash.
4. Deploy the selected prior Green release.
5. Do not delete or rewrite payment ledger rows.
6. Verify `/v1/health` and runtime identity.
7. Confirm payment/cache/telemetry databases open without migration errors.
8. Reconcile any transactions left in `PRESENTED`, `FULFILLMENT_STARTED`, `FULFILLED`, or `SETTLEMENT_PENDING`.
9. Run a non-paying health/preflight validation before restoring paid traffic.
10. Record the rollback evidence and incident outcome.

## Persistence recovery

The authoritative operational databases are configured by:

- `REPOGUARD_CACHE_DB`
- `REPOGUARD_TELEMETRY_DB`
- `REPOGUARD_PAYMENT_DB`

The production container defaults them to files under `/data`. Restart or redeploy must preserve that mounted volume. Loss of the persistent payment database is a release-blocking incident because idempotency/replay/reconciliation history would become incomplete.

## Schema compatibility

No destructive persistence migration is permitted on the release critical path without:

- backup;
- forward migration test;
- rollback compatibility assessment;
- explicit migration evidence.

## Recovery verification

A recovery is complete only when:

- runtime identity is known;
- persistent data is readable;
- unresolved payment states are enumerated;
- no duplicate settlement is initiated;
- health/preflight succeeds;
- evidence is attached to the release/incident record.
