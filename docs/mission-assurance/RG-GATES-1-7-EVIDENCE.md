# RG-GATES-1-7 — RAPHAEL Security Evidence Package

**Governance:** RAPHAEL Master Spec v1.6 + RAPHAEL Security Governance Protocol  
**Scope:** limited public-repository RepoGuard x402 launch profile  
**Validated source SHA:** `61f5518f0caa161a172325c40b1d8c333155bd5d`  
**GitHub Actions:** `40458378397` / CI #437  
**Backend result:** 167 passed, 3 warnings  
**Gate 8:** NOT AUTHORIZED

## Package Result

The Gates 1–7 evidence package is complete and machine-readable. Package completion does **not** mean every gate has passed.

Generated artifact:

`raphael-security-gates-1-7.json`

Release-evidence artifact:

- artifact ID: `12713701400`
- digest: `sha256:847f9690677599d30db51185b65461dad697e04fb70a64468cdb79bdf7991018`

Additional same-SHA evidence:

- repository security artifact `12712744416` — `sha256:f5f4709479665bc2b9345e8a8beace367c1f4a7b7125ef20f1a19389580155aa`
- container provenance artifact `12713328731` — `sha256:2b4c4de39ec1cf2b1ed42767196487860db09daf59d9237014e22be823b66150`
- hostile staging artifact `12713775444` — `sha256:a7235e5015ad162e5d1cb165db261b0a8555b579523fd42c0da5dc9d9c8f95e9`

## Gate Status

### Gate 1 — Repository Integrity: BLOCKED

Passed:

- exact-source-head CI;
- full fetched-history Gitleaks scan;
- exact-fingerprint policy for three intentional secret-detection regression fixtures;
- zero unexpected secret-history findings.

Remaining blockers:

- `x402-production` branch protection / required-check enforcement requires repository administration;
- repository is currently public and public-source disposition requires explicit Principal approval or a visibility change.

The three allowed historical Gitleaks findings are fake scanner test strings in `backend/tests/test_scanner_regression.py`, committed in `5f74b053abf759fdd32fca1ceb84efefc9f1f27b`. They are allowlisted only by exact historical fingerprint in `docs/security/GITLEAKS_TEST_FIXTURE_ALLOWLIST.json`. Any additional finding fails CI.

### Gate 2 — Application Attack Surface: PASS

Verified:

- legacy/demo/internal route blocking;
- request body and field bounds;
- closed-by-default CORS;
- HSTS;
- Content-Security-Policy;
- Cache-Control `no-store`;
- clickjacking, MIME, referrer and permissions headers;
- fail-closed provider/scanner error behavior.

### Gate 3 — Identity and Tenant Isolation: PASS for authorized launch scope

Verified:

- public-preview mode secure by default;
- only public-scan providers allowed;
- optional provider credentials suppressed.

Not applicable to the limited public-preview launch scope:

- authenticated/private repository access;
- customer multi-tenant private data plane.

Those capabilities remain deferred and may not inherit this Gate 3 result if later enabled.

### Gate 4 — Secrets and Network Boundaries: BLOCKED

Passed:

- SSRF/private/metadata-network containment;
- provider-host binding;
- redirect containment;
- credential forwarding restrictions;
- public-preview credential suppression;
- structured secret redaction.

Remaining blocker:

- deployed Railway/platform egress policy verification.

### Gate 5 — Supply Chain and Runtime: BLOCKED

Passed:

- locked Python and Node dependency audits;
- non-root runtime;
- actual final rootfs HIGH/CRITICAL vulnerability gate;
- package-management tooling removed from final runtime;
- exact source/OCI/release provenance.

Remaining blocker:

- exact Railway deployed artifact/runtime identity and platform infrastructure security verification.

### Gate 6 — Abuse and Adversarial Testing: BLOCKED

Passed application-owned controls:

- bounded concurrent scan capacity;
- hardened commerce per-client/per-route request rate window with HTTP 429 + Retry-After;
- provider failure circuit breaker with cooldown + Retry-After;
- dedicated hostile-staging suite.

Remaining blockers:

- edge/WAF/platform abuse policy verification;
- live load/resource acceptance.

### Gate 7 — Data / Payment / Recovery: BLOCKED

Passed engineering controls:

- secret-safe structured operational evidence;
- payment state machine;
- replay/idempotency protections;
- settlement reconciliation semantics;
- receipt issuance;
- cache/payment/telemetry persistence;
- cross-process restart behavior;
- operator, incident, credential-rotation and rollback/recovery runbooks.

Remaining blockers:

- live Base Sepolia settlement/replay/cache acceptance;
- Railway volume restart/redeploy recovery evidence.

## Gate 8

Gate 8 remains human-only and is not authorized by this package.

## Truth Rule

This record is evidence for source SHA `61f5518f0caa161a172325c40b1d8c333155bd5d`. Material changes to source, dependencies, workflow, deployment, payment configuration, security boundaries or runtime may require refreshed evidence under the RAPHAEL freshness ledger.
