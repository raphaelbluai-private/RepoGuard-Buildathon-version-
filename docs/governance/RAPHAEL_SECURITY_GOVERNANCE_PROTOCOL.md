# RAPHAEL SECURITY GOVERNANCE PROTOCOL

**Version:** 1.0  
**Status:** Canonical Universal Security Control Template  
**Applies To:** Web apps, APIs, SaaS platforms, AI/agent systems, mobile apps, desktop apps, cloud services, payment systems, automation tools, and repository-hosted products  
**Primary Objective:** Require every build to discover, verify, repair, retest, and document security weaknesses before launch and throughout operation.  
**Final Launch Authority:** Authorized human principal

---

## 0. Operating Rule

This protocol is not a passive checklist. When an authorized agent finds a security issue, the required loop is:

```text
DISCOVER
   ↓
IDENTIFY ATTACK SURFACE
   ↓
THREAT MODEL
   ↓
SCAN
   ↓
VERIFY FINDING
   ↓
ROOT-CAUSE ANALYSIS
   ↓
REPAIR
   ↓
REGRESSION TEST
   ↓
HOSTILE / ADVERSARIAL TEST
   ↓
RE-SCAN
   ↓
COLLECT EVIDENCE
   ↓
MARK VERIFIED / BLOCKED
   ↓
HUMAN GO / NO-GO
```

An agent SHALL NOT mark a control Green merely because code exists, a dependency was installed, a test was written but not run, CI passed on another commit, a local build worked, or a setting appears configured. Security claims require evidence tied to the relevant build and runtime.

---

# 1. Status Language

Use only these RAPHAEL security states:

```text
🟩 VERIFIED
Implemented, tested, and supported by reproducible evidence.

🟨 CONTROLLED / EVIDENCE PENDING
Control exists or risk is bounded, but required production, hostile-test, or operational evidence is incomplete.

🟥 BLOCKING
Material vulnerability, missing control, unsafe configuration, unverified trust boundary, or unresolved risk that blocks launch or expansion.

🟪 LEGACY / REMOVE
Obsolete, duplicate, demo-only, superseded, or unnecessary production attack surface.
```

No PASS label may override an unresolved 🟥 item.

---

# 2. Governing Security Baseline

At the start of every review, determine the current applicable security baseline. Do not assume historical repository guidance is current.

Map this protocol where relevant to:

- NIST Secure Software Development Framework (SSDF), using the latest final revision as binding reference and newer drafts as advisory unless explicitly adopted;
- OWASP Application Security Verification Standard (ASVS), current stable release;
- OWASP Top 10, current release;
- OWASP API Security Top 10, current release;
- OWASP mobile guidance for mobile applications;
- OWASP LLM/agentic security guidance when AI agents or models are present;
- CIS Controls and applicable CIS Benchmarks;
- OpenSSF Scorecard practices;
- SLSA software-supply-chain guidance;
- official security guidance for the actual deployment platform;
- applicable privacy, contractual, payment, sector, or regulatory obligations.

**2026 reference:** NIST SP 800-218 SSDF v1.1 is final; SSDF v1.2 remains draft guidance unless and until finalized or explicitly adopted.

This protocol does not claim certification under any external framework.

---

# 3. Security Mission Card

Before scanning or modifying a repository, create or update:

```yaml
security_mission:
  application_name: ""
  repository: ""
  branch: ""
  commit_sha: ""
  application_type: ""
  deployment_platform: ""
  environments: [development, staging, production]
  public_exposure: "none | private | limited-preview | public"
  tenant_model: "single | multi-tenant | none"
  data_classes: []
  secrets_present: "yes | no | unknown"
  payments_present: "yes | no"
  ai_agents_present: "yes | no"
  privileged_connectors_present: "yes | no"
  private_repository_access: "yes | no"
  security_owner: ""
  launch_authority: ""
  review_date: ""
```

Unknown deployment identity or unknown trust boundaries are findings until resolved.

---

# 4. Platform and Application Discovery

Identify the real architecture from code and deployment evidence:

- languages/frameworks;
- frontend/backend boundaries;
- public APIs/routes;
- authentication and authorization;
- databases/storage/caches/queues;
- file upload/download paths;
- payments;
- AI models and agents;
- repository providers;
- third-party APIs/connectors;
- OAuth apps and webhooks;
- cloud services and IAM;
- infrastructure-as-code;
- containers/orchestration;
- DNS/CDN/WAF;
- email/notifications;
- analytics/telemetry;
- secret stores;
- CI/CD;
- signing systems;
- deployment targets;
- admin/operator surfaces.

Produce a concise flow:

```text
CLIENT / AGENT
      ↓
EDGE / CDN / WAF
      ↓
PUBLIC API / FRONTEND
      ↓
AUTHN / AUTHZ
      ↓
APPLICATION SERVICES
      ↓
DATA / CACHE / FILES
      ↓
THIRD-PARTY / CLOUD / PAYMENT / MODEL PROVIDERS
```

---

# 5. Data Classification

Classify all handled data:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
CUSTOMER-CONFIDENTIAL
SECRET / CREDENTIAL
FINANCIAL / PAYMENT
PERSONAL DATA
HIGH-RISK REGULATED DATA
```

For each class, record ingress, processing location, storage location, authorized readers/writers, agent/service access, tenant boundaries, encryption requirements, retention, deletion, backup behavior, log restrictions, exports, and third-party recipients.

Do not collect or retain sensitive data merely because it might be useful later.

---

# 6. Threat Model

At minimum consider anonymous Internet attackers, malicious authenticated users, compromised customer accounts, rogue autonomous agents, hostile crawlers, malicious repositories/files, prompt injection, malicious dependencies, compromised CI runners, leaked keys, insiders, stolen operator accounts, payment replay/fraud, cross-tenant attempts, SSRF/internal network probing, resource exhaustion, source-code extraction, compromised third parties, and DNS/supply-chain compromise.

Document assets, threat actors, trust boundaries, attack paths, controls, residual risk, and evidence.

---

# 7. Repository and Source-Code Security

Verify repository visibility is intentional; proprietary backend logic is private unless approved; permissions follow least privilege; production/release branches are protected; required CI checks block merge; direct production pushes are restricted where practical; critical release tags are protected; release commits/tags are attributable; `.gitignore` excludes secrets/runtime artifacts; and demo/debug source is excluded from production attack surface unless required.

### Mandatory secret history review

Run current-tree and history-aware secret scanning where practical. Rotate or revoke exposed secrets. Deleting a leaked secret from the current file is not complete remediation.

---

# 8. Dependency and Supply-Chain Security

Verify lockfiles, version constraints, vulnerability scanning, abandoned critical-package review, trusted registries, install/lifecycle scripts where relevant, minimal dependency sets, trusted/pinned CI actions, controlled base images, container scans, SBOMs/provenance for higher-assurance releases, and regression/security testing after dependency upgrades.

A practical critical dependency exploit is launch-blocking unless mitigated and formally accepted.

---

# 9. Secrets and Credential Governance

Never commit or expose passwords, private keys, seed phrases, API keys, OAuth client secrets, database credentials, signing keys, payment private material, cloud service-account keys, or production tokens.

Require secret managers/protected runtime variables, least-privilege scopes, environment separation, short-lived credentials where supported, rotation/revocation procedures, secret-safe health endpoints/errors/telemetry/CI logs/reports, and secret-redaction tests.

### Credential forwarding rule

Credentials SHALL only be sent to the specific provider, hostname, account, and protocol for which they were issued. Caller-controlled URLs must never cause service credentials to be sent to untrusted hosts.

---

# 10. Authentication Security

Production auth must not be demo auth. Use accepted adaptive password hashing where passwords exist, MFA for privileged accounts where appropriate, secure token generation, session expiration/revocation, safe recovery, rate limits, brute-force protection, and stronger privileged-role controls where warranted. OTP codes must never be returned by production APIs.

---

# 11. Authorization and Access Control

Every sensitive operation must enforce authorization server-side. Test horizontal/vertical privilege escalation, IDOR/BOLA, role bypass, tenant bypass, resource ownership, admin/internal access, guessed IDs, and unauthorized state changes.

Frontend visibility controls are not authorization controls.

---

# 12. Multi-Tenant and Client Data Isolation

For every multi-customer system, prove Tenant A cannot read, write, enumerate, or trigger server-credential access to Tenant B data/resources. Test database, cache, object storage, queues, workers, search/vector indexes, telemetry, exports, backups, agent memory, and connector credentials.

A failed cross-tenant isolation test is a Critical launch blocker.

---

# 13. API Security

Enumerate public routes and verify authentication/authorization scope, schema validation, body/batch limits, content types, identifier/URL/path validation, rate and concurrency limits, timeouts, mass-assignment protection, safe errors, internal/debug route protection, versioned contracts, and idempotency for retriable state-changing/payment operations.

Test injection, BOLA/IDOR, broken auth, excessive exposure, resource exhaustion, unsafe third-party consumption, and misconfiguration.

---

# 14. SSRF and Outbound Network Security

Any caller-supplied URL/repository/webhook/import/callback/remote resource is an SSRF boundary.

At minimum: permit required protocols only; prefer HTTPS; validate hostname against provider; resolve and reject loopback/private/link-local/multicast/reserved/cloud-metadata addresses; validate redirects; defend against DNS rebinding where relevant; restrict outbound ports/egress where possible; prevent provider credentials from reaching caller-controlled hosts; reject embedded URL credentials; and log only safe destination metadata.

---

# 15. Input Validation and Injection Protection

Review SQL/NoSQL/OS/shell/template/LDAP/XPath/header/CRLF injection, path traversal, archive traversal, XXE where XML exists, unsafe deserialization, regex DoS, unsafe YAML, dynamic code execution, malicious filenames, and MIME/content mismatch.

Prefer structured APIs and parameterized execution over string construction.

---

# 16. File, Upload, and Archive Security

Define allowed file classes, size limits, MIME/signature validation where relevant, randomized storage names, traversal prevention, non-executable upload storage, archive safety, decompression/file-count caps, zip-bomb defenses, tenant isolation, and retention/deletion.

---

# 17. Database and Storage Security

Verify private network posture where possible, least-privilege credentials, environment separation, encryption in transit/at rest where appropriate, protected/encrypted backups, object-level authorization, RLS where appropriate and tested, controlled destructive operations, migration rollback/forward-recovery, sensitive-data minimization, and retention/deletion.

---

# 18. Encryption and Key Management

Require TLS for public traffic, certificate validation, maintained cryptographic primitives, no homegrown crypto without review, externalized signing/encryption keys, key IDs/rotation where needed, and recovery/revocation procedures.

Hashing is not encryption. Hashing is not signing. Signing is not access control.

---

# 19. Logging, Telemetry, and Privacy

Do not log passwords, authorization headers, session tokens, private keys, seed phrases, payment signatures, customer secrets, raw private repository contents unless strictly required/protected, or high-risk personal data without explicit need.

Prefer correlation IDs, hashes, safe account IDs, status codes, timings, provider IDs, event types, and redacted errors. Verify access control, retention, deletion, and incident usefulness.

---

# 20. Payment and Financial Security

Never store wallet private keys/seed phrases in code/logs. Validate network and receiver, fail closed on unsupported networks, bind payment to purchased operation where possible, implement idempotency/replay protection, verify settlement where required, prevent double execution/charging, minimize payment evidence, separate testnet/mainnet, require explicit human authorization for real-value transition, monitor anomalies, and verify webhook/callback signatures where supported.

A payment system that can double-charge an idempotent retry is launch-blocking.

---

# 21. AI / Agent Security

Treat model/retrieved input as hostile unless proven otherwise. Separate untrusted content, trusted instructions, and privileged action authority. Use least-privilege tools/connectors, explicit authorization for destructive/high-risk actions, credential redaction, restricted model-triggered destinations, independently validated tool arguments, deterministic security evidence that cannot be overridden by model output, and chain-of-custody for higher-assurance workflows.

Test whether rogue agents can request unauthorized customer resources, enumerate internal routes, obtain credentials, induce another agent/tool to reveal secrets, bypass payment, call unapproved hosts, cause destructive writes, trigger excessive spend/loops, or override policy via prompt text.

---

# 22. Third-Party Connectors, OAuth, and Webhooks

Document data exchanged, use minimum scopes, validate webhook signatures/replay controls, secure OAuth state/PKCE where applicable, protect/store/revoke tokens correctly, separate customer authorization contexts, and restrict connector calls to approved hosts.

---

# 23. Frontend / Browser Security

Review XSS, unsafe HTML, CSP, clickjacking, secure cookies, SameSite, CSRF, CORS, browser secret storage, exposed source maps, client-bundled environment variables, open redirects, third-party scripts, dependency integrity, and download safety.

`Access-Control-Allow-Origin: *` must be intentional. Machine-to-machine API access does not require unrestricted browser CORS.

---

# 24. Mobile Security

Where applicable, protect secrets from app bundles, use secure token storage, enforce TLS verification, validate exported components/deep links/WebViews, protect signing keys, remove debug settings, and test local data deletion.

---

# 25. Desktop Security

Where applicable, verify update/installer integrity, signing, local credential storage, filesystem permissions, IPC/localhost/protocol handlers, auto-update validation, Electron/Tauri/WebView hardening, local DB protection, untrusted file handling, and uninstall/data deletion.

---

# 26. Cloud and Deployment-Platform Security

Identify the real provider and run provider-specific review for IAM, secrets, network exposure, private networking, storage, backups, build/deploy source, service accounts, logs, TLS/domains, egress, runtime identity, region/data residency where relevant, rollback, health checks, resource limits, and current advisories.

Do not assume provider defaults are secure for the application.

---

# 27. Container Security

Use minimal base images, non-root runtime, controlled image versions/digests where practical, vulnerability scans, no unnecessary runtime build tools/OS packages, no privileged containers or Docker socket, dropped unnecessary capabilities, read-only root filesystem where feasible, limited writable paths, resource constraints, no secrets in layers, and isolated temporary untrusted files.

---

# 28. Network / Edge / Abuse Protection

Use layered controls:

```text
EDGE PROTECTION
      ↓
APPLICATION RATE LIMIT
      ↓
ACCOUNT / WALLET / TENANT LIMIT
      ↓
RESOURCE LIMIT
      ↓
DOWNSTREAM CIRCUIT BREAKER
```

Evaluate CDN/WAF/DDoS protections where appropriate, per-IP/account/wallet throttling, concurrency/expensive-operation quotas, request/scan limits, queue backpressure, downstream rate awareness, bounded retries with jitter, and agentic/metered cost limits.

---

# 29. CI/CD and Release Security

Review workflow permissions and triggers, fork-secret exposure, least-privilege CI secrets, trusted/pinned actions, reproducible dependency installation, release artifact/source identity, tests against exact release commit, artifact digest/provenance, deployment identity reconciliation, rollback, release authorization, and non-bypassable security gates.

---

# 30. Error Handling and Fail-Closed Behavior

Security-sensitive failures should fail closed. Required non-passing conditions include unknown identity, invalid signature, missing credential, ambiguous authorization, tenant ownership not proven, policy conflict, unknown runtime identity, unsettled payment, persistence failure, unavailable signing key, unsafe URL, failed file validation, unverified webhook, critical vulnerability, and failed security tests.

Errors should identify corrective action without leaking secrets.

---

# 31. Security Headers and Server Configuration

Evaluate HSTS, Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, frame-ancestors/clickjacking controls, Permissions-Policy, secure cookies, and cache-control for sensitive responses. Configure and test correctly rather than adding headers mechanically.

---

# 32. Security Test Matrix

Minimum applicable matrix:

```text
[ ] Static code analysis
[ ] Dependency vulnerability scan
[ ] Secret scan
[ ] Repository history secret scan
[ ] Infrastructure/config scan
[ ] Container scan
[ ] API authorization tests
[ ] Cross-tenant isolation tests
[ ] SSRF tests
[ ] Injection tests
[ ] Path traversal/file tests
[ ] Authentication abuse tests
[ ] Rate/resource exhaustion tests
[ ] Payment replay/idempotency tests
[ ] Prompt-injection / rogue-agent tests
[ ] Logging/redaction tests
[ ] Production configuration inspection
[ ] Deployment identity verification
[ ] Backup/recovery test where required
```

Tool output is evidence, not automatic truth. Findings must be triaged and verified.

---

# 33. Hostile / Adversarial Test Environment

Use staging/controlled environments before production where practical. No real customer data; test accounts; test payment value/network where possible; disposable/scoped credentials; production-like security configuration; monitoring; and a clear kill control.

Test malformed/oversized inputs, high rate/concurrency, unauthorized object/tenant IDs, internal/private URLs, redirect SSRF, malicious repository/file names, shell metacharacters, malicious archives, credential exfiltration, payment replay/duplicates, expired/revoked tokens, prompt injection, rogue-agent instructions, and provider timeouts/failures.

---

# 34. Auto-Repair Rules for Build Agents

When authorized, an agent finding a security issue SHALL confirm it, find root cause, assess production-path impact, add/update a regression test where feasible, apply the smallest complete root-cause repair, rerun targeted/security/adversarial tests, run broader regression when needed, and record evidence.

Agents SHALL NOT repeatedly patch symptoms, weaken controls to pass tests, disable TLS verification, suppress findings without justification, make repos public for convenience, broaden credentials for convenience, expose secrets to complete tests, self-authorize production, or mark untested repairs Green.

---

# 35. Security Change Control

A change affecting a trust boundary requires security review, including private repo access, OAuth, databases/storage, uploads, payment networks/mainnet, LLMs/agents, connectors, auth changes, public endpoints, multi-tenancy, cloud migration, webhooks, or admin capability. Document new assets, threats, controls, tests, and evidence.

---

# 36. Vulnerability Severity and Response

```text
CRITICAL
Likely or demonstrated compromise of secrets, authorization, tenant isolation, production control, financial assets, or arbitrary code execution.

HIGH
Serious practical exploit path with meaningful confidentiality, integrity, or availability impact.

MEDIUM
Material weakness with bounded impact or meaningful prerequisites.

LOW
Defense-in-depth weakness or limited-impact issue.
```

Default launch policy: unresolved Critical = launch blocked; unresolved practical High = launch blocked unless formally risk-accepted; Medium = repair where reasonable or document mitigation/owner/date; Low = backlog permitted if no compounded risk.

---

# 37. Data Retention, Deletion, and Recovery

Define and test retention, deletion trigger, backups, caches, logs, derived data/embeddings, exports, post-deletion agent/memory behavior where controllable, and legal/contractual exceptions. Backups must not become a weaker security copy of production.

---

# 38. Incident Response

Minimum process:

```text
DETECT
  ↓
CONTAIN
  ↓
REVOKE / ROTATE
  ↓
PRESERVE EVIDENCE
  ↓
ERADICATE ROOT CAUSE
  ↓
RECOVER
  ↓
VALIDATE
  ↓
DOCUMENT LESSONS
```

Maintain a security owner, credential revocation, rollback, impact assessment, evidence preservation, provider shutdown, payment-disable control where applicable, and post-incident review.

---

# 39. Business Logic and Intellectual Property Protection

Keep proprietary backend logic server-side; keep production backend repositories private unless explicitly approved; avoid shipping proprietary algorithms/secrets in client bundles where avoidable; minimize unnecessary diagnostic detail; protect admin/debug interfaces; use least-privilege repository access; separate public SDK/client code from private server implementation where useful; and use licensing/IP protections alongside technical controls.

Browser-delivered JavaScript is observable.

---

# 40. Platform-Specific Security Adapter

Append provider-specific IAM, secrets, network exposure, storage, logs, build/deploy provenance, backup/recovery, findings, and verification evidence. Consult current official provider guidance because defaults/features change.

---

# 41. Required Security Evidence

Every Green control should identify control ID, status, repository, branch, commit SHA, environment, validation time/method, command or external evidence record, result, artifact/log reference, and reviewer. Never store secrets in evidence.

---

# 42. Security Requirements Traceability

Use stable IDs such as `RSGP-REQ-001` and map Requirement → Threat/Risk → Control → Code/Configuration → Test → Evidence → Status. No requirement is VERIFIED without evidence.

---

# 43. Mandatory Pre-Launch Security Gates

## Gate 1 — Repository Integrity
Repository ownership/visibility intentional; production branch protected; secret history reviewed; CI mandatory.

## Gate 2 — Application Attack Surface
Public routes inventoried; legacy/demo/debug paths removed or protected; input boundaries validated; errors safe.

## Gate 3 — Identity and Tenant Isolation
Authentication/authorization verified where required; tenant isolation tested; private customer resources cannot cross trust boundaries.

## Gate 4 — Secrets and Network Boundaries
Secrets externalized; least privilege; SSRF protections verified; credential forwarding restricted; egress controlled.

## Gate 5 — Supply Chain and Runtime
Dependency scan dispositioned; container/runtime hardened; deployed artifact matches intended commit; infrastructure security reviewed.

## Gate 6 — Abuse and Adversarial Testing
Rate/resource limits verified; hostile and rogue-agent tests run where applicable; Critical/High findings resolved or formally accepted.

## Gate 7 — Data / Payment / Recovery
Retention/deletion reviewed; logs redacted; payment controls tested; backup/recovery and incident controls established.

## Gate 8 — Human Launch Authorization
Only an authorized human records final production go/no-go.

---

# 44. Presumptive Launch Blockers

Known exposed secrets; cross-tenant access; broken auth/authz; arbitrary credential forwarding; SSRF into internal/private/metadata networks; RCE; practical command/SQL injection; privileged public admin/debug routes; unprotected private customer data; unverified production deployment identity; practical Critical dependency exploits; payment replay/double-charge; signing/private-key exposure; unnecessary dangerous runtime privilege; and security controls bypassed to meet schedule.

---

# 45. Security Master Tree Template

```text
RAPHAEL SECURITY MASTER TREE

LEGEND
🟩 ready / verified
🟨 partially complete / evidence pending
🟥 needs building / launch blocker
🟪 legacy / remove

APPLICATION
│
├── REPOSITORY SECURITY
├── SECRET MANAGEMENT
├── AUTHENTICATION
├── AUTHORIZATION / TENANT ISOLATION
├── API SECURITY
├── NETWORK / SSRF / EGRESS
├── DATA / STORAGE / PRIVACY
├── AI / AGENT SECURITY
├── PAYMENT SECURITY
├── SUPPLY CHAIN
├── CONTAINER / CLOUD RUNTIME
├── CI / RELEASE SECURITY
├── HOSTILE TESTING
└── FINAL SECURITY GATE
    ├── Gates 1-7 evidence
    └── Gate 8 human authorization
```

---

# 46. Continuous Post-Launch Security

Monitor vulnerabilities, auth abuse, unusual API volume, payment anomalies, new endpoints/connectors, tenant isolation after data-layer changes, SSRF after network/provider changes, credential rotation/IAM, backups/recovery, full security gates before major releases, periodic adversarial testing, and evidence-backed incident lessons. Material architecture changes reset applicable controls until retested.

---

# 47. Agent Execution Directive

When this file exists in a repository, an authorized development/security agent SHALL inspect actual repository/deployment interfaces, data flows, credentials, dependencies, and runtime; determine applicable controls; verify with reproducible evidence; repair verified vulnerabilities within authorized scope; add regression coverage; retest; never weaken controls or expose secrets; never self-authorize launch; and report live build state rather than stale documentation or chat memory.

---

# 48. Final Security Report Template

Report build identity, overall classification, Critical/High findings, repaired controls, tests, hostile tests, tenant isolation, secret/credential result, supply chain, runtime/cloud, payment, AI/agent result, remaining risks, evidence, Gates 1-7, and Gate 8 human authorization state.

---

# 49. Definition of Security Green

Security Green requires identified attack surfaces; resolved/formally accepted Critical/High findings; demonstrated client/tenant isolation where applicable; scoped/protected/leak-tested credentials; protected external URL/file/input trust boundaries; reviewed supply chain; verified runtime/deployment configuration; hostile testing for high-risk boundaries; evidence mapped to exact release/runtime; and final human launch authorization.

**Engineering Green is not automatically Production-Authorized Green.**

---

# 50. Core RAPHAEL Security Principle

> **Assume every public input can be hostile, every credential can become a target, every trust boundary must be proven, every customer must be isolated from every other customer, and every Green claim must be supported by evidence. Build securely, fail closed, repair root causes, and never let speed outrank confidentiality, integrity, availability, or human launch authority.**