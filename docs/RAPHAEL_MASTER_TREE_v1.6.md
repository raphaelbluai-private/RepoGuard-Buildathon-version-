# REPOGUARD RAPHAEL MASTER TREE v1.6

**Governing Authority:** RAPHAEL Master Spec v1.6  
**Canonical Repo:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Canonical Branch:** `x402-production`  
**Primary Ship Path:** hardened public-repository scanner + x402 rail  

```text
LEGEND
🟩 ready / verified
🟨 partially complete / evidence pending
🟥 needs building / launch blocker
🟪 legacy / remove

REPO GUARD
│
├── 🟩 GOVERNANCE
│   ├── 🟩 RAPHAEL Master Spec v1.6 installed
│   ├── 🟩 RAPHAEL Security Governance Protocol installed
│   ├── 🟩 continuous completion task installed
│   ├── 🟩 .build-state.json exists
│   ├── 🟩 BUILD_HANDOFF exists
│   ├── 🟩 SESSION_RECOVERY_PROTOCOL exists
│   ├── 🟩 G0 reconciliation record exists
│   └── 🟩 Master Tree persisted in repo
│
├── 🟩 DETERMINISTIC SCANNER CORE
│   ├── 🟩 repository scanner
│   ├── 🟩 deterministic findings
│   ├── 🟩 scoring
│   ├── 🟩 SAFE_TO_SHIP / NEEDS_REVIEW / SHIP_BLOCKED
│   ├── 🟩 remediation output
│   └── 🟩 scanner regression suite
│
├── 🟩 PROVIDER ACQUISITION FOUNDATION
│   ├── 🟩 canonical repository snapshot
│   ├── 🟩 GitHub
│   ├── 🟩 GitLab
│   ├── 🟩 Bitbucket
│   ├── 🟩 Azure DevOps
│   ├── 🟩 Codeberg
│   ├── 🟩 SourceHut
│   ├── 🟩 SourceForge
│   ├── 🟨 Gitea / Gogs / OneDev self-hosted mode
│   │   └── disabled by default for public launch
│   ├── 🟨 AWS CodeCommit
│   │   └── authenticated acceptance deferred outside public-preview scope
│   └── 🟨 Google Cloud Source Repositories
│       └── authenticated acceptance deferred outside public-preview scope
│
├── 🟩 LAUNCH-SCOPE SSRF / CREDENTIAL HARDENING
│   ├── 🟩 HTTPS-only full clone URLs
│   ├── 🟩 hosted-provider hostname binding
│   ├── 🟩 embedded URL credentials rejected
│   ├── 🟩 private/loopback/link-local/reserved destination blocking
│   ├── 🟩 DNS-resolved destination validation
│   ├── 🟩 Git redirects disabled for outbound acquisition
│   ├── 🟩 auth header scoped to intended HTTPS host
│   ├── 🟩 self-hosted provider URLs disabled by default
│   └── 🟩 regression tests for credential exfiltration / SSRF boundary
│
├── 🟩 PUBLIC-PREVIEW PRIVATE-DATA CONTAINMENT
│   ├── 🟩 public preview is secure default
│   ├── 🟩 auth-required providers blocked from preview
│   ├── 🟩 optional provider credentials suppressed in preview
│   ├── 🟩 private repository access excluded from launch scope
│   └── 🟥 future customer-scoped private-repository authorization
│
├── 🟩 PUBLIC API ATTACK-SURFACE HARDENING
│   ├── 🟩 legacy free `/api/scan` blocked in hardened composition
│   ├── 🟩 demo auth routes blocked
│   ├── 🟩 demo trigger/resolve routes blocked
│   ├── 🟩 internal diagnostic routes blocked
│   ├── 🟩 old verifier route blocked
│   ├── 🟩 request field bounds
│   ├── 🟩 request body size cap
│   ├── 🟩 wildcard CORS stripped from hardened commerce surface
│   └── 🟨 production security-header set
│       └── remaining verification / configuration work
│
├── 🟨 RESOURCE / ABUSE PROTECTION
│   ├── 🟩 provider Git timeouts
│   ├── 🟩 extracted-file max size
│   ├── 🟩 request max size
│   ├── 🟩 bounded concurrent scan gate
│   ├── 🟨 application rate limiting
│   │   └── legacy limiter exists; hardened commerce-specific policy requires launch verification
│   ├── 🟥 edge/WAF or platform-level abuse policy verification
│   ├── 🟥 live load/resource test
│   └── 🟥 circuit-breaker / provider-failure acceptance evidence
│
├── 🟨 CONTAINER / RUNTIME SECURITY
│   ├── 🟩 non-root `repoguard` runtime user
│   ├── 🟩 dedicated temporary directory
│   ├── 🟩 `/data` ownership prepared for runtime persistence
│   ├── 🟩 minimal Python runtime image
│   ├── 🟩 Git + CA certificates only as required OS additions
│   ├── 🟨 production container build gate
│   │   └── must pass on final release candidate
│   ├── 🟥 container/image vulnerability review
│   └── 🟥 runtime privilege/resource verification on deployed candidate
│
├── 🟩 AGENT COMMERCE API
│   ├── 🟩 /v1/health
│   ├── 🟩 /v1/repoguard/products
│   ├── 🟩 /v1/repoguard/preflight
│   ├── 🟩 /v1/repoguard/verify
│   ├── 🟩 /v1/repoguard/safe-to-ship
│   ├── 🟩 /v1/repoguard/scan
│   ├── 🟩 /v1/repoguard/explain
│   └── 🟩 /v1/repoguard/attest
│
├── 🟩 PRODUCT LADDER
│   ├── 🟩 Preflight — free
│   ├── 🟩 Verify Commit — $0.01
│   ├── 🟩 Safe-to-Ship — $0.03
│   ├── 🟩 Repository Scan — $0.07
│   ├── 🟩 Explain Findings — $0.10
│   └── 🟩 Attestation — $0.15
│
├── 🟨 X402 PAYMENT RAIL
│   ├── 🟩 x402 v2 middleware
│   ├── 🟩 product-specific pricing
│   ├── 🟩 Base Sepolia network support
│   ├── 🟩 payment challenge path
│   ├── 🟩 invalid-payment engineering regressions
│   ├── 🟩 mainnet interlock governance
│   ├── 🟨 settlement telemetry foundation
│   ├── 🟥 current hardened-release real Sepolia settlement
│   ├── 🟥 repeat same-SHA payment/cache evidence
│   ├── 🟥 payment retry/idempotency live evidence
│   ├── 🟥 external autonomous-agent purchase
│   └── 🟥 Base mainnet Principal authorization
│
├── 🟩 PROVENANCE / BASIC ATTESTATION FOUNDATION
│   ├── 🟩 scan ID
│   ├── 🟩 repository/provider identity
│   ├── 🟩 commit SHA
│   ├── 🟩 scanner/ruleset/adapter version
│   ├── 🟩 canonical result hash
│   └── 🟩 basic attestation output
│
├── 🟥 FULL VERIFICATION RECEIPT v1
│   ├── 🟥 canonical receipt schema
│   ├── 🟥 previous-receipt lineage
│   ├── 🟥 policy binding
│   ├── 🟥 payment binding
│   ├── 🟥 cryptographic signing
│   ├── 🟥 signature verification
│   ├── 🟥 key rotation metadata
│   └── 🟥 durable receipt retrieval
│
├── 🟥 GOVERNED POLICY ENGINE
│   ├── 🟥 policy schema
│   ├── 🟥 canonical policy hash
│   ├── 🟥 path/glob scope
│   ├── 🟥 precedence
│   ├── 🟥 conflict detection
│   ├── 🟥 supersession
│   └── 🟥 fail-closed resolution
│
├── 🟥 AGENT / TOOL CHAIN OF CUSTODY
│   ├── 🟥 principal identity
│   ├── 🟥 agent/model/tool identity
│   ├── 🟥 invocation identity
│   ├── 🟥 evidence hashes
│   └── 🟥 explicit UNAVAILABLE states
│
├── 🟥 GOVERNED LEARNINGS
│   ├── 🟥 append-only history
│   ├── 🟥 attribution
│   ├── 🟥 precedence
│   ├── 🟥 supersession/dispute states
│   └── 🟥 deterministic governing-record selection
│
├── 🟥 REPOSITORY ↔ RUNTIME RECONCILIATION
│   ├── 🟥 authorized source commit
│   ├── 🟥 deployed artifact/image digest
│   ├── 🟥 deployed source identity
│   ├── 🟥 configuration hash without secrets
│   ├── 🟥 drift/stale deployment detection
│   └── 🟥 fail-closed unknown runtime identity
│
├── 🟨 CI / RELEASE ASSURANCE
│   ├── 🟩 frontend typecheck
│   ├── 🟩 frontend build
│   ├── 🟩 backend compile
│   ├── 🟩 correctness lint
│   ├── 🟩 backend regression suite
│   ├── 🟩 security regressions included
│   ├── 🟩 production container build gate exists
│   ├── 🟥 protected `x402-production` branch
│   ├── 🟥 required checks enforced by branch protection
│   └── 🟥 signed/verifiably attributable release process
│
├── 🟥 PRODUCTION REALIZATION / OPERATIONS
│   ├── 🟥 exact release manifest
│   ├── 🟥 artifact provenance / SBOM or justified equivalent
│   ├── 🟥 exact Railway deployment identity reconciliation
│   ├── 🟥 persistent-state restart verification
│   ├── 🟥 rollback / recovery evidence
│   ├── 🟥 structured operational alerts
│   ├── 🟥 operator runbook
│   ├── 🟥 incident / credential rotation runbook
│   ├── 🟥 performance budgets and results
│   └── 🟥 evidence freshness ledger
│
├── 🟥 HOSTILE STAGING / SECURITY ACCEPTANCE
│   ├── 🟥 malicious provider-host test
│   ├── 🟥 localhost/private/metadata SSRF test
│   ├── 🟥 redirect/destination-change test
│   ├── 🟥 credential leak test
│   ├── 🟥 oversized request/repository test
│   ├── 🟥 concurrent overload test
│   ├── 🟥 secret/log-redaction test
│   ├── 🟥 payment replay/retry test
│   └── 🟥 hostile security gate report
│
├── 🟥 REAL USER / EXTERNAL AGENT ACCEPTANCE
│   ├── 🟥 autonomous discovery
│   ├── 🟥 product/price understanding
│   ├── 🟥 x402 challenge handling
│   ├── 🟥 payment
│   ├── 🟥 result receipt
│   └── 🟥 no undocumented developer intervention
│
├── 🟪 LEGACY / REMOVE OR RECONCILE
│   ├── 🟪 old Buildathon-only assumptions
│   ├── 🟪 stale GitHub-only README narrative
│   ├── 🟪 old single-price scan references
│   ├── 🟪 legacy app commercial route implementation
│   ├── 🟪 demo OTP behavior
│   ├── 🟪 demo breach-control routes
│   ├── 🟪 wildcard CORS inside legacy sub-app source
│   └── 🟪 stale changelog state
│
└── CURRENT CRITICAL PATH
    ├── 🟨 G0 canonical reconciliation — substantially complete
    ├── 🟨 G1 launch-scope security hardening — active
    ├── 🟥 hostile staging acceptance
    ├── 🟥 G2 x402 contract/idempotency reconciliation
    ├── 🟥 G3–G4 v1.6 Production Realization evidence
    ├── 🟥 G5 live hardened Base Sepolia acceptance
    ├── 🟥 G6 external-agent acceptance
    ├── 🟥 G7 Gates 1–7 evidence package
    ├── 🟥 Gate 8 Principal limited-launch authorization
    └── 🟥 G8 continuous full-completion after x402 launch
```

## Truth Rule

A status moves to 🟩 only with current evidence tied to the relevant source/artifact/environment. Historical GREEN does not automatically survive a material security, payment, deployment, dependency, or runtime change.
