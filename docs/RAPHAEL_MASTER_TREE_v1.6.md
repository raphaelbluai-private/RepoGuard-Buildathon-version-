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
│   ├── 🟩 production container build gate — exact-head CI #331 verified
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
├── 🟨 PAYMENT OPERATIONS ASSURANCE
│   ├── 🟩 durable transaction state machine — CI #285 verified
│   ├── 🟩 x402 verify/settle lifecycle hook binding — CI #285 verified
│   ├── 🟩 idempotency / duplicate fulfillment protection — engineering verified; live proof pending separately
│   ├── 🟩 payment-proof replay protection — engineering verified; live hostile proof pending separately
│   ├── 🟩 scanner-failure-after-payment protection — engineering verified; live proof pending separately
│   ├── 🟩 settlement-timeout reconciliation semantics — engineering verified; live drill pending separately
│   ├── 🟩 payment telemetry metrics + internal aggregate surface — engineering verified
│   ├── 🟩 facilitator failure matrix — engineering verified; measured/live facilitator evidence remains open
│   ├── 🟩 x402 SDK pinned to qualified engineering version 2.22.0
│   ├── 🟩 post-presentation automatic facilitator failover prohibited
│   ├── 🟥 measured facilitator reliability
│   ├── 🟥 authoritative facilitator rate/volume limits
│   ├── 🟥 live Base Sepolia idempotency/replay/reconciliation acceptance
│   └── 🟥 production/mainnet facilitator qualification
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
├── 🟨 REPOSITORY ↔ RUNTIME RECONCILIATION
│   ├── 🟩 authorized source commit contract + exact-SHA release manifest
│   ├── 🟨 deployed artifact/image digest — CI image identity proven; Railway deployment pending
│   ├── 🟨 deployed source identity — OCI/runtime contract built; live Railway reconciliation pending
│   ├── 🟩 configuration hash without secrets
│   ├── 🟩 drift/stale deployment detection — authorized-SHA mismatch fails closed
│   └── 🟩 fail-closed unknown runtime identity option
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
├── 🟨 PRODUCTION REALIZATION / OPERATIONS
│   ├── 🟩 exact release manifest — generated and SHA-verified in CI
│   ├── 🟩 artifact provenance / justified dependency-inventory equivalent
│   ├── 🟨 exact Railway deployment identity reconciliation — runtime contract built; live proof pending
│   ├── 🟩 persistent-state restart verification — cache/payment/telemetry cross-process recovery proven
│   ├── 🟩 rollback / recovery evidence — recovery contract + runbook
│   ├── 🟨 structured operational alerts — schema/emission verified; live delivery sink pending
│   ├── 🟩 operator runbook
│   ├── 🟩 incident / credential rotation runbook
│   ├── 🟨 performance budgets and results — budgets codified; live load results pending
│   └── 🟩 evidence freshness ledger
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
    ├── 🟨 G2 payment operations assurance — engineering GREEN; live Sepolia/facilitator evidence pending
    ├── 🟨 G3–G4 v1.6 Production Realization — engineering substantially GREEN; live Railway/load/alert evidence pending
    ├── 🟥 G5 live hardened Base Sepolia acceptance
    ├── 🟥 G6 external-agent acceptance
    ├── 🟥 G7 Gates 1–7 evidence package
    ├── 🟥 Gate 8 Principal limited-launch authorization
    └── 🟥 G8 continuous full-completion after x402 launch
```

## Truth Rule

A status moves to 🟩 only with current evidence tied to the relevant source/artifact/environment. Historical GREEN does not automatically survive a material security, payment, deployment, dependency, or runtime change.
