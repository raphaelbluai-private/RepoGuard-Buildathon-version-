# RG-G3-G4 — Production Realization Engineering

## Mission

Create the release, runtime-identity, persistence, recovery, operational-alert, performance-budget, and evidence controls required to turn RepoGuard's Green engineering build into a deployment that can be reconciled and operated safely.

## Implemented engineering controls

- persistent SQLite paid-scan cache;
- production `/data` defaults for scan cache, commerce telemetry, and payment ledger;
- cross-process restart persistence test;
- safe runtime configuration hash;
- source/deployment/image identity contract;
- fail-closed runtime identity option for authorized releases;
- safe public runtime identity view and internal full identity view;
- OCI source revision label in production image;
- structured operational alert schema and payment/scanner alert emission;
- explicit verify/fulfillment/settlement/total performance budgets;
- exact-SHA release manifest generator;
- machine-readable Python and Node production dependency inventories;
- container image inspection/ID evidence artifact;
- operator runbook;
- incident/credential rotation/rollback/recovery runbook;
- evidence-freshness ledger.

## Evidence classification

Engineering can be marked Green only after exact-head CI proves:

- frontend dependency audit/typecheck/build;
- Python dependency audit/compile/lint/tests;
- cross-process persistence recovery;
- production container build;
- embedded OCI source revision;
- release-manifest source SHA verification;
- dependency-evidence artifact generation.

The following remain live/platform gates and cannot be Green from CI alone:

- exact Railway deployment identity reconciliation;
- Railway persistent-volume restart/redeploy test;
- deployed runtime privilege/resource-limit verification;
- live structured-alert delivery/notification sink;
- live performance/load results;
- platform/edge abuse controls;
- live Base Sepolia acceptance;
- external-agent purchase;
- Gate 8 authorization.

## SBOM-equivalent disposition

For the current pre-launch candidate, CI emits machine-readable production dependency inventories from both committed lock graphs together with exact lockfile hashes in the release manifest and container inspection evidence. This is accepted as the current justified dependency-provenance equivalent. A formal standardized SBOM may replace or supplement it before wider production authorization without changing product behavior.


## Verified engineering evidence

Validated code SHA: `1fe40efabe5375e7f2b48e9a83246d6b55ca3b40`

GitHub Actions: run `40438665107` / CI #331

Result:

- frontend dependency audit: PASS
- frontend typecheck/build: PASS
- Python dependency audit: PASS
- compile/lint: PASS
- backend regression/security/payment/production-realization suite: 138 PASS
- cross-process cache/payment/telemetry recovery: PASS
- runtime authorized-release drift rejection: PASS
- production container build: PASS
- embedded OCI source revision verification: PASS
- container provenance artifact: PASS
- exact-SHA release manifest: PASS
- machine-readable production dependency inventories: PASS
- release evidence upload: PASS

**Engineering status:** GREEN for internally verifiable G3–G4 controls.

**Live/platform status:** YELLOW/RED where Railway deployment identity, platform volume restart, live alert delivery, live performance/load, edge abuse controls, or payment-network evidence is required.
