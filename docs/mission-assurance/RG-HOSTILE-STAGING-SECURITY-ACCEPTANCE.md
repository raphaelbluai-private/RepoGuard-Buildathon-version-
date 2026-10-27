# RG-HOSTILE-STAGING — Non-Live Security Acceptance

## Scope

This evidence package validates RepoGuard's hardened public launch surface without submitting a real Base Sepolia or mainnet payment.

Validated source SHA: `3b47b345e73142db624001b2bb4d9230af56f3fe`

GitHub Actions: `40441963199` / CI #403

## Acceptance evidence

The dedicated hostile-staging gate passed for:

- malicious hosted-provider hostname substitution;
- localhost/private/link-local/metadata-address SSRF attempts;
- DNS resolution to private/metadata destinations;
- Git redirect / destination-change containment;
- provider credential scoping and public-preview credential suppression at the Git transport boundary;
- oversized request rejection before scan execution;
- concurrent scan saturation fail-closed behavior;
- recursive operational-alert secret redaction;
- duplicate/replayed payment-proof rejection without performing a live settlement.

The full backend regression/security/payment/operations suite also passed: **158 tests**.

## Container security evidence

The production runtime is built non-root and package-management tooling is removed after dependency installation.

The CI container gate:

1. builds the exact canonical source SHA;
2. verifies the OCI source revision label;
3. smoke-imports RepoGuard, FastAPI and x402;
4. verifies active `urllib3==2.8.0`;
5. verifies `pip`, `setuptools`, and `wheel` are absent from the final runtime;
6. exports the final container root filesystem;
7. scans the actual rootfs with Trivy for fixed HIGH/CRITICAL vulnerabilities;
8. stores the vulnerability/provenance evidence.

CI #403 passed this gate with no eligible HIGH/CRITICAL fixed findings.

This rootfs scan intentionally evaluates the final runtime filesystem rather than inherited third-party image SBOM records that were observed to contain stale packaging-tool metadata.

## Release identity correction

GitHub pull-request workflows expose a synthetic merge SHA through `github.sha`. RepoGuard release evidence now uses:

`REPOGUARD_SOURCE_SHA = pull_request.head.sha || github.sha`

Every CI checkout, container tag, OCI revision, hostile-staging report, release manifest, readiness report, release-assurance report and artifact name is bound to the same canonical source SHA.

## Remaining acceptance boundaries

This engineering evidence does **not** prove or authorize:

- live Base Sepolia settlement/replay behavior;
- Railway runtime/volume/resource controls;
- edge/WAF abuse controls;
- live load/performance;
- branch protection / required-check enforcement;
- signed release governance;
- approval of the repository's current public visibility;
- external autonomous-agent purchase;
- Gate 8 launch authorization.

Those remain separate RAPHAEL gates.
