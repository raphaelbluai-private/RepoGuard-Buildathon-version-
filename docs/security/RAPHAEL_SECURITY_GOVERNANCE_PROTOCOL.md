# RAPHAEL SECURITY GOVERNANCE PROTOCOL

**Version:** 1.0<br>
**Status:** Canonical Universal Security Control Template<br>
**Applies To:** Web apps, APIs, SaaS platforms, AI/agent systems, mobile apps, desktop apps, cloud services, payment systems, automation tools, and repository-hosted products<br>
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

For each class, record:

- ingress;
- processing location;
- storage location;
- authorized readers/writers;
- agent/service access;
- tenant boundaries;
- encryption requirements;
- retention;
- deletion;
- backup behavior;
- log restrictions;
- exports;
- third-party recipients.

Do not collect or retain sensitive data merely because it might be useful later.

---

# 6. Threat Model

At minimum consider:

- anonymous Internet attacker;
- malicious authenticated user;
- compromised customer account;
- rogue autonomous agent;
- hostile crawler;
- malicious repository;
- malicious file/upload;
- prompt injection;
- malicious dependency;
- compromised CI runner;
- leaked API key;
- insider threat;
- stolen operator account;
- payment replay/fraud;
- cross-tenant access attempt;
- SSRF/internal network probing;
- denial-of-service/resource exhaustion;
- source-code/business-logic extraction;
- compromised third-party provider;
- DNS/supply-chain compromise.

Document assets, threat actors, trust boundaries, attack paths, controls, residual risk, and evidence.

---

# 7. Repository and Source-Code Security

Verify:

- repository visibility is intentional;
- proprietary backend logic is private unless explicitly approved otherwise;
- repository permissions follow least privilege;
- inactive collaborators are removed;
- production/release branches are protected;
- required CI checks block merge;
- direct production pushes are restricted where practical;
- force-push/deletion restrictions are appropriate;
- critical release tags are protected;
- release commits/tags are attributable;
- CODEOWNERS or equivalent exists where useful;
- `.gitignore` excludes secrets, local DBs, temp files, generated credentials, and runtime artifacts;
- demo/debug source is not part of production attack surface without need.

### Mandatory secret history review

Run current-tree and history-aware secret scanning where practical. Rotate or revoke any exposed secret. Deleting a leaked secret from the current file is not complete remediation.

---

# 8. Dependency and Supply-Chain Security

Verify:

- lockfiles exist and are used;
- dependency versions are intentionally constrained;
- known vulnerabilities are scanned;
- abandoned critical packages are identified;
- typo-squatting risk is considered;
- packages use trusted registries;
- lifecycle/install scripts are reviewed where relevant;
- unnecessary packages are removed;
- CI actions/plugins are trusted and pinned appropriately;
- base container images are minimal and controlled;
- container images are vulnerability-scanned;
- SBOMs are generated for higher-assurance releases where appropriate;
- build provenance/attestation is preserved where appropriate;
- dependency upgrades must pass regression/security tests.

A practical critical dependency exploit is launch-blocking unless mitigated and formally accepted.

---

# 9. Secrets and Credential Governance

Never commit or expose:

- passwords;
- private keys;
- seed phrases;
- API keys;
- OAuth client secrets;
- database credentials;
- signing keys;
- payment private material;
- cloud service-account keys;
- production tokens.

Require:

- secret manager/protected runtime variables;
- least-privilege scopes;
- separation of development/staging/production credentials;
- short-lived credentials where supported;
- rotation/revocation procedures;
- no secret values in health endpoints;
- no secrets in exception output;
- no secrets in telemetry or CI logs;
- no secrets in reports;
- no credentials embedded in URLs;
- secret-redaction tests.

### Credential forwarding rule

Credentials SHALL only be sent to the specific provider, hostname, account, and protocol for which they were issued. Caller-controlled URLs must never cause service credentials to be sent to untrusted hosts.

---

# 10. Authentication Security

Where authentication exists:

- production auth must not be demo auth;
- passwords use accepted adaptive hashing;
- MFA is available/required for privileged accounts where appropriate;
- OTP codes are never returned by production APIs;
- tokens are securely generated;
- sessions expire;
- refresh/revocation behavior is defined;
- logout works;
- recovery does not bypass security;
- login/verification endpoints are rate-limited;
- brute-force protections exist;
- privileged roles receive stronger protection where warranted.

---

# 11. Authorization and Access Control

Every sensitive operation must enforce authorization server-side.

Test:

- horizontal privilege escalation;
- vertical privilege escalation;
- IDOR/BOLA;
- role bypass;
- tenant bypass;
- resource ownership;
- admin/internal route access;
- guessed object IDs;
- unauthorized state changes.

Frontend visibility controls are not authorization controls.

---

# 12. Multi-Tenant and Client Data Isolation

For every multi-customer system, prove:

```text
Tenant A cannot read Tenant B data.
Tenant A cannot write Tenant B data.
Tenant A cannot enumerate Tenant B objects.
Tenant A cannot cause shared service credentials to access Tenant B resources.
Tenant A cannot retrieve Tenant B logs, reports, files, scans, receipts, prompts, embeddings, cache entries, or exports.
```

Test isolation in:

- application queries;
- database RLS/policies;
- cache keys;
- object storage;
- queues;
- workers;
- search/vector indexes;
- telemetry;
- exports;
- backups;
- agent memory;
- connector credentials.

Any demonstrated cross-tenant leak is Critical and launch-blocking.

---

# 13. API Security

For every public API:

- inventory routes;
- define auth requirements;
- define authorization scope;
- validate schemas;
- reject dangerous/unknown fields where appropriate;
- cap request/body/batch size;
- enforce content types;
- validate identifiers, URLs, filenames and paths;
- enforce rate limits;
- enforce concurrency limits;
- enforce timeouts;
- prevent mass assignment;
- avoid stack traces;
- use typed safe errors;
- disable unused endpoints;
- protect debug/internal routes;
- version public contracts;
- use idempotency for retriable payment/state-changing operations when appropriate.

Test injection, BOLA/IDOR, broken auth, excessive data exposure, resource exhaustion, and unsafe third-party API consumption.

---

# 14. SSRF and Outbound Network Security

Any feature accepting a URL, repository, webhook destination, callback, image URL, import source, or remote resource is an SSRF boundary.

Required controls:

- allow only required protocols;
- prefer HTTPS;
- validate hostname against claimed provider;
- reject embedded URL credentials;
- resolve/validate destinations where feasible;
- reject loopback;
- reject private ranges;
- reject link-local;
- reject multicast/reserved ranges;
- reject cloud metadata endpoints;
- validate redirect destinations;
- address DNS rebinding risk where relevant;
- restrict outbound ports;
- use egress allowlists where possible;
- never attach provider credentials to caller-controlled domains;
- log safe destination metadata without secrets.

---

# 15. Input Validation and Injection Protection

Review all externally controlled input for:

- SQL/NoSQL injection;
- OS/shell/command injection;
- template injection;
- LDAP/XPath injection;
- header/CRLF injection;
- path traversal;
- archive traversal/Zip Slip;
- XXE when XML is used;
- unsafe deserialization;
- regex DoS;
- unsafe YAML loaders;
- dynamic code execution;
- malicious filenames;
- MIME/content mismatch.

Prefer structured APIs and parameterized execution over string construction.

---

# 16. File, Upload, and Archive Security

If uploads exist:

- define allowed types;
- enforce file/total limits;
- validate MIME/signatures where relevant;
- randomize storage names;
- block traversal;
- isolate uploads from executable app paths;
- disable execution;
- scan high-risk uploads where appropriate;
- cap decompressed archive size/file count;
- defend against zip bombs;
- prevent cross-tenant file access;
- define retention/deletion.

---

# 17. Database and Storage Security

Verify:

- DB is not publicly reachable unless required;
- credentials are least privilege;
- dev/staging/prod are separated;
- encryption in transit is used;
- encryption at rest is appropriate;
- backups are encrypted/access-controlled;
- authorization applies to every customer object;
- RLS is tested where used;
- destructive operations are controlled;
- migrations have rollback/forward recovery;
- sensitive fields are minimized;
- retention/deletion works;
- exports are protected.

---

# 18. Encryption and Key Management

Verify:

- TLS is mandatory for public production traffic;
- certificate validation is enabled;
- insecure downgrade is blocked;
- standard maintained primitives are used;
- homegrown cryptography requires formal review;
- signing keys are protected outside source;
- key IDs and rotation exist where signed evidence is used;
- recovery/rotation procedures exist.

Hashing is not encryption. Hashing is not signing. Signing is not authorization.

---

# 19. Logging, Telemetry, and Privacy

Do not log:

- passwords;
- raw authorization headers;
- session tokens;
- private keys/seed phrases;
- payment signatures;
- customer secrets;
- private repo contents without explicit protected need;
- high-risk personal data without explicit need.

Prefer correlation IDs, hashes, safe account IDs, status codes, timings, event types, and redacted errors.

Verify log access, retention, deletion, and incident usefulness.

---

# 20. Payment and Financial Security

For payment systems:

- never store wallet private keys or seed phrases in app source/logs;
- validate network and receiver;
- fail closed on unsupported networks;
- bind payment to the purchased operation where practical;
- use replay/idempotency protections;
- verify settlement before fulfillment where required;
- prevent double execution/double charging;
- minimize stored payment evidence;
- separate testnet/mainnet;
- require explicit human authorization for real-value/mainnet transition;
- monitor settlement failures/anomalies;
- verify payment webhooks cryptographically where supported.

Double-charge/replay flaws are launch-blocking.

---

# 21. AI / Agent Security

Treat model inputs and retrieved content as untrusted.

Separate:

```text
UNTRUSTED CONTENT
from
TRUSTED INSTRUCTIONS
from
PRIVILEGED ACTION AUTHORITY
```

Require:

- repository/file/web content cannot become system authority;
- least-privilege tool permissions;
- explicit authorization for destructive/high-risk actions;
- secrets excluded/redacted from model context unless strictly needed;
- model-triggered destinations restricted;
- tool arguments validated independently of model output;
- LLMs cannot override deterministic evidence;
- models cannot approve their own waivers;
- agent/tool custody is captured for high-assurance workflows;
- prompt injection is tested across files, repos, web pages, email, tickets, and retrieved docs;
- human authorization remains mandatory for launch, privilege elevation, destructive operations, and unbounded financial spending.

### Rogue-agent tests

Test whether an agent can:

- request another customer's resources;
- enumerate internal endpoints;
- obtain provider credentials;
- trick tools/agents into leaking secrets;
- bypass payment;
- contact unauthorized hosts;
- perform destructive writes;
- cause unbounded loops/spend;
- override security policy through prompt text.

---

# 22. Third-Party Connectors, OAuth, and Webhooks

For every connector:

- document data sent/received;
- minimize scopes;
- prefer user/repo-scoped over workspace-wide credentials;
- validate webhook signatures;
- prevent replay where relevant;
- rotate secrets;
- validate redirect URIs;
- use OAuth state/PKCE where applicable;
- store tokens securely;
- separate each customer's authorization;
- revoke on disconnect;
- prevent one customer's token accessing another's data;
- restrict connector calls to approved hostnames.

---

# 23. Frontend / Browser Security

Review:

- XSS;
- unsafe HTML;
- CSP;
- clickjacking protections;
- secure/SameSite cookies;
- CSRF for cookie-authenticated changes;
- CORS;
- browser storage of secrets;
- exposed source maps;
- sensitive env vars bundled client-side;
- open redirects;
- third-party scripts;
- file-download safety.

`Access-Control-Allow-Origin: *` must be intentional. Machine-to-machine APIs do not require unrestricted browser CORS.

---

# 24. Mobile Security

If applicable:

- no secrets embedded in APK/IPA;
- secure token storage;
- TLS verification;
- exported Android components intentional;
- deep links validated;
- WebViews hardened;
- sensitive screenshot/clipboard behavior reviewed;
- signing keys protected;
- debug settings removed from release;
- local data deletion tested.

---

# 25. Desktop Security

If applicable:

- update integrity;
- installer signing;
- credential storage;
- filesystem permissions;
- IPC/localhost services;
- protocol handlers;
- update-source validation;
- Electron/Tauri/WebView hardening;
- untrusted file handling;
- uninstall/data deletion.

---

# 26. Cloud and Deployment-Platform Security

Identify the actual deployment provider and run a provider-specific review for Railway, AWS, Azure, GCP, Vercel, Cloudflare, Supabase, Firebase, Kubernetes, Docker, or others.

Verify applicable:

- service visibility;
- secrets;
- IAM;
- network exposure/private networking;
- persistent volumes;
- backups;
- build/deploy source;
- service accounts;
- logs;
- domains/TLS;
- egress;
- runtime identity;
- data region requirements;
- rollback;
- health checks;
- resource limits;
- provider security advisories.

Do not assume platform defaults are secure for the application.

---

# 27. Container Security

For containerized workloads:

- minimal base image;
- non-root runtime;
- controlled image versions/digests where practical;
- vulnerability scan;
- remove unnecessary build/runtime tools;
- avoid privileged mode;
- avoid Docker socket;
- drop unnecessary capabilities;
- read-only root filesystem where feasible;
- constrain writable paths;
- resource limits;
- no secrets in image layers;
- isolate temporary untrusted files;
- keep runtime patched.

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

Evaluate CDN/WAF, DDoS protections, per-IP and per-account/wallet limits, concurrency caps, expensive-operation quotas, request-size caps, job timeouts, backpressure, bounded retries, downstream-provider limits, and agent cost/spend ceilings.

---

# 29. CI/CD and Release Security

Verify:

- workflows are reviewed;
- branch triggers are intentional;
- fork PRs cannot trivially access secrets;
- CI secrets are least privilege;
- CI permissions are minimized;
- third-party actions are trusted/pinned;
- dependency installation is reproducible;
- production artifacts originate from authorized commits;
- security tests run on release commit;
- artifacts have hashes/digests;
- deployment identity reconciles to repo identity;
- rollback exists;
- production deployment has appropriate authorization;
- security gates cannot be silently skipped.

---

# 30. Error Handling and Fail-Closed Behavior

Security-sensitive unknowns should fail closed.

Examples:

- unknown repository/provider;
- invalid signature;
- missing required credential;
- ambiguous authorization;
- tenant ownership not proven;
- policy conflict;
- unknown runtime identity;
- unsettled payment;
- persistence failure;
- signing key unavailable;
- unsafe destination URL;
- unverified webhook;
- unacceptable dependency vulnerability;
- security-test failure.

Errors should be actionable without leaking sensitive implementation details.

---

# 31. Security Headers and Server Configuration

Evaluate applicable:

- HSTS;
- Content-Security-Policy;
- X-Content-Type-Options;
- Referrer-Policy;
- frame-ancestors/clickjacking controls;
- Permissions-Policy;
- secure cookie attributes;
- cache-control for sensitive responses.

Configure and test; do not add headers mechanically if they break required functionality.

---

# 32. Security Test Matrix

Minimum applicable matrix:

```text
[ ] Static code analysis
[ ] Dependency vulnerability scan
[ ] Secret scan
[ ] Repository-history secret scan
[ ] Infrastructure/config scan
[ ] Container scan
[ ] API authorization tests
[ ] Cross-tenant isolation tests
[ ] SSRF tests
[ ] Injection tests
[ ] Path traversal/file tests
[ ] Authentication abuse tests
[ ] Rate-limit/resource-exhaustion tests
[ ] Payment replay/idempotency tests
[ ] Prompt-injection / rogue-agent tests
[ ] Logging/redaction tests
[ ] Production configuration inspection
[ ] Deployment identity verification
[ ] Backup/recovery test where required
```

Tool output is evidence, not automatic truth. Findings must be verified and triaged.

---

# 33. Hostile / Adversarial Test Environment

High-risk testing should use staging or another controlled environment before broad production exposure.

Use:

- no real customer data;
- test accounts;
- test payment network/value where possible;
- tightly scoped disposable credentials;
- production-like security configuration;
- monitoring;
- clear stop/kill control.

Test malformed/oversized payloads, rate/concurrency abuse, unauthorized IDs, cross-tenant IDs, private/internal URLs, redirect SSRF, malicious names/files, shell metacharacters, malicious archives, credential exfiltration, payment replay, duplicate requests, revoked tokens, prompt injection, rogue-agent instructions, and downstream failure/timeout behavior.

---

# 34. Auto-Repair Rules for Build Agents

When authorized, an agent finding a security issue SHALL:

1. Confirm the finding.
2. Identify root cause.
3. Determine production-path impact.
4. Add/update a regression test where feasible.
5. Apply the smallest complete root-cause repair.
6. Re-run targeted tests.
7. Re-run relevant security scans.
8. Run the associated hostile case.
9. Run broader regression if shared infrastructure changed.
10. Record evidence.

The agent SHALL NOT:

- repeatedly patch symptoms without root-cause analysis;
- weaken controls to make tests pass;
- disable TLS verification;
- suppress findings without justification;
- make a repo public for convenience;
- broaden credentials for convenience;
- expose secrets to complete a test;
- replace human production authorization with model judgment;
- mark untested repairs Green.

---

# 35. Security Change Control

Any change that alters a trust boundary resets the relevant security gates.

Examples:

- private repository access;
- OAuth;
- new database/storage;
- file uploads;
- new payment network;
- mainnet/real funds;
- new LLM/agent;
- new connector;
- authentication changes;
- new public endpoint;
- multi-tenancy;
- cloud migration;
- webhooks;
- new admin capability.

Document new assets, threats, controls, tests, and evidence.

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

Default launch policy:

- unresolved Critical: 🟥 launch blocked;
- unresolved practical High: 🟥 launch blocked unless formally risk-accepted by authorized human;
- Medium: repair before launch where reasonable, otherwise document owner/mitigation/date;
- Low: backlog permitted if no compounded risk.

---

# 37. Data Retention, Deletion, and Recovery

Define and test:

- retention period;
- deletion trigger;
- backups;
- caches;
- logs;
- derived data/embeddings;
- exports;
- post-deletion agent/memory behavior where controllable;
- legal/contractual retention exceptions.

Backups must not become a weaker copy of production.

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

Maintain a security owner, credential revocation process, rollback process, impact assessment, evidence preservation method, provider shutdown control, payment-disable control where applicable, and post-incident review.

---

# 39. Business Logic and Intellectual Property Protection

Security cannot make a public service impossible to imitate, but it can reduce unnecessary exposure.

For proprietary products:

- keep proprietary backend logic server-side;
- keep production backend repositories private unless explicitly approved;
- avoid shipping proprietary algorithms/secrets in client bundles when avoidable;
- minimize unnecessary diagnostic detail;
- protect admin/debug interfaces;
- use least-privilege repository access;
- separate public SDK/client code from private server implementation where useful;
- use contractual/licensing/IP protection alongside technical controls.

Browser-delivered JavaScript must be considered observable.

---

# 40. Platform-Specific Security Adapter

Append this section for the actual deployment platform:

```markdown
## PLATFORM SECURITY ADAPTER — <PLATFORM NAME>

### Identity / IAM
- ...

### Secrets
- ...

### Network exposure
- ...

### Database/storage
- ...

### Logs
- ...

### Build/deploy provenance
- ...

### Backup/recovery
- ...

### Provider-specific security findings
- ...

### Verification evidence
- ...
```

Consult current official platform security guidance during every review because provider features/defaults change.

---

# 41. Required Security Evidence

Every Green claim should record evidence:

```yaml
evidence:
  control_id: RSGP-XXX
  status: VERIFIED
  repository: owner/repo
  branch: release
  commit_sha: abc123
  environment: staging|production
  validation_time: ISO-8601
  validation_method: ""
  command_or_external_record: ""
  result: PASS
  artifact_or_log_reference: ""
  reviewer: ""
```

Never place secrets in evidence records.

---

# 42. Security Requirements Traceability

Use stable IDs:

```text
RSGP-REQ-001
RSGP-REQ-002
RSGP-REQ-003
...
```

Map:

```text
Requirement
   ↓
Threat / Risk
   ↓
Control
   ↓
Code / Configuration
   ↓
Test
   ↓
Evidence
   ↓
Status
```

No requirement is VERIFIED without evidence.

---

# 43. Mandatory Pre-Launch Security Gates

## Gate 1 — Repository Integrity

- repository ownership/visibility intentional;
- production branch protected;
- secret history reviewed;
- CI mandatory.

## Gate 2 — Application Attack Surface

- public routes inventoried;
- legacy/demo/debug paths removed or protected;
- input boundaries validated;
- errors are safe.

## Gate 3 — Identity and Tenant Isolation

- auth verified where required;
- authorization verified;
- tenant isolation tested;
- private customer resources cannot cross trust boundaries.

## Gate 4 — Secrets and Network Boundaries

- secrets externalized;
- least privilege;
- SSRF protections verified;
- credential forwarding restricted;
- egress controlled.

## Gate 5 — Supply Chain and Runtime

- dependency scan dispositioned;
- container/runtime hardened;
- deployed artifact matches intended commit;
- infrastructure security reviewed.

## Gate 6 — Abuse and Adversarial Testing

- rate/resource limits verified;
- hostile tests run;
- rogue-agent tests run where applicable;
- Critical/High findings resolved or formally accepted.

## Gate 7 — Data / Payment / Recovery

- retention/deletion reviewed;
- logs redacted;
- payment controls tested where applicable;
- backup/recovery and incident controls established.

## Gate 8 — Human Launch Authorization

Only an authorized human records the final production go/no-go decision.

---

# 44. Presumptive Launch Blockers

```text
🟥 Known exposed production secret
🟥 Cross-tenant access
🟥 Broken authentication/authorization
🟥 Arbitrary credential forwarding
🟥 SSRF into private/internal/cloud-metadata networks
🟥 Remote code execution
🟥 Practical command/SQL injection
🟥 Public privileged admin/debug endpoint
🟥 Unprotected private customer data
🟥 Unverified production deployment identity
🟥 Practical Critical dependency exploit
🟥 Payment replay/double-charge flaw
🟥 Signing/private-key exposure
🟥 Unnecessary dangerous runtime privilege
🟥 Security controls bypassed to meet schedule
```

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
│   └── ...
│
├── SECRET MANAGEMENT
│   └── ...
│
├── AUTHENTICATION
│   └── ...
│
├── AUTHORIZATION / TENANT ISOLATION
│   └── ...
│
├── API SECURITY
│   └── ...
│
├── NETWORK / SSRF / EGRESS
│   └── ...
│
├── DATA / STORAGE / PRIVACY
│   └── ...
│
├── AI / AGENT SECURITY
│   └── ...
│
├── PAYMENT SECURITY
│   └── ...
│
├── SUPPLY CHAIN
│   └── ...
│
├── CONTAINER / CLOUD RUNTIME
│   └── ...
│
├── CI / RELEASE SECURITY
│   └── ...
│
├── HOSTILE TESTING
│   └── ...
│
└── FINAL SECURITY GATE
    ├── Gates 1-7 evidence
    └── Gate 8 human authorization
```

---

# 46. Continuous Post-Launch Security

After launch:

- monitor vulnerability advisories;
- patch dependencies;
- monitor auth abuse;
- monitor unusual API volume;
- monitor payment anomalies;
- review new endpoints/connectors;
- rerun tenant-isolation tests after data-layer changes;
- rerun SSRF tests after networking/provider changes;
- rotate credentials on schedule and after suspected exposure;
- review IAM periodically;
- verify backups/recovery;
- rerun the full security gate before major releases;
- perform periodic adversarial testing;
- preserve evidence-backed incident lessons.

Material architecture changes reset applicable controls to unverified until retested.

---

# 47. Agent Execution Directive

When this file exists in a repository, an authorized development/security agent SHALL interpret it as follows:

> Inspect the actual repository, deployment configuration, public interfaces, data flows, credentials, dependencies, and runtime. Determine which RAPHAEL Security Governance Protocol controls apply. Verify existing controls with reproducible evidence. For verified vulnerabilities within authorized scope, repair root causes, add regression coverage, retest, and document evidence. Do not weaken controls to obtain Green. Do not expose secrets. Do not make production-affecting destructive changes or authorize launch without human authority. Mark unknowns and deferred external evidence honestly. Security status must reflect the live build, not stale documentation or conversation summaries.

---

# 48. Final Security Report Template

```markdown
# RAPHAEL SECURITY GATE REPORT

## Build Identity
- Repository:
- Branch:
- Commit:
- Environment:
- Deployment ID / artifact digest:

## Classification
- Overall: 🟩 / 🟨 / 🟥

## Critical Findings
- ...

## High Findings
- ...

## Controls Repaired
- ...

## Tests Performed
- ...

## Hostile Tests
- ...

## Client/Tenant Isolation Result
- ...

## Secret/Credential Result
- ...

## Supply-Chain Result
- ...

## Runtime/Cloud Result
- ...

## Payment Result
- ...

## AI/Agent Result
- ...

## Remaining Risks
- ...

## Evidence
- ...

## Launch Decision
- Gates 1-7:
- Gate 8 human authorization: NOT AUTHORIZED / AUTHORIZED
```

---

# 49. Definition of Security Green

A build is Security Green only when:

1. applicable attack surfaces are identified;
2. Critical/High vulnerabilities are resolved or formally risk-accepted;
3. client/tenant data isolation is demonstrated where applicable;
4. credentials are scoped, protected, and leak-tested;
5. external URLs/files/inputs cannot cross forbidden trust boundaries;
6. supply-chain risks are reviewed;
7. runtime/deployment configuration is verified;
8. hostile testing is complete for applicable high-risk boundaries;
9. evidence maps to the exact release commit/runtime;
10. final human launch authorization is recorded.

**Engineering Green is not automatically Production-Authorized Green.**

---

# 50. Core RAPHAEL Security Principle

> **Assume every public input can be hostile, every credential can become a target, every trust boundary must be proven, every customer must be isolated from every other customer, and every Green claim must be supported by evidence. Build securely, fail closed, repair root causes, and never let speed outrank confidentiality, integrity, availability, or human launch authority.**
