# REPO GUARD CONTINUOUS COMPLETION — CONTINUATION BUILD TASK

**RAPHAEL MASTER SPEC v1.6 GOVERNED**  
**Task ID:** `RG-V16-CONTINUOUS-COMPLETION-001`  
**Mission Weight:** Critical  
**Canonical Repository:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Canonical Branch:** `x402-production`  
**Primary Ship-Path:** x402 rail launch  
**Execution Mode:** Continuous completion; do not stop after a milestone while required work remains executable.

---

## 1. GOVERNING AUTHORITY

RAPHAEL Master Spec v1.6 is the presiding governance, mission-assurance, continuity, security, evidence, production-realization, operational-readiness, and release-authorization authority for this task and all subsequent RepoGuard build work.

Do not override RAPHAEL v1.6 with:

- prior assumptions;
- historical GREEN status;
- convenience refactors;
- prototype/demo behavior;
- prior chat state;
- stale handoffs;
- unsupported previous launch claims;
- pressure to deploy before evidence exists.

Repository evidence controls. The live canonical branch, current HEAD, governing documents, build-state record, Master Tree, continuity files, CI evidence, security evidence, deployed-runtime identity, and executable production path must remain reconciled throughout execution.

Companion authority:

- `docs/governance/RAPHAEL_MASTER_SPEC_v1.6_GOVERNANCE.md`
- RAPHAEL Security Governance Protocol
- existing RepoGuard mission-assurance records where not superseded by v1.6

---

## 2. PRIMARY MISSION

Drive the current RAPHAEL MASTER TREE from required 🟥 status to 🟩 and bring the RepoGuard x402 rail to the earliest **safe, evidence-backed, v1.6-verifiable launch point**.

The build must distinguish:

1. **Limited x402 launch scope** — earliest lawful/secure production scope that can satisfy v1.6; and
2. **Full platform completion scope** — all remaining required red items converted to Green in dependency order after the initial x402 launch gate.

A narrow production authorization is permitted only when its exact scope is explicit and all fatal flaws inside that scope are cleared.

The recommended earliest launch scope is:

> RepoGuard public-repository deterministic scanner + x402 paid product rail, with private-repository access disabled until customer/tenant authorization isolation is verified.

---

## 3. NON-STOP EXECUTION RULE

After this task begins, execution continues automatically through the named work packages in dependency order.

Do not stop merely because:

- one package reaches Green;
- a document is complete;
- one CI run passes;
- a deployment succeeds;
- a runtime/external gate is temporarily unavailable;
- a credential/account must later be supplied by the Principal.

If an external dependency is unavailable, mark that specific gate `BLOCKED` or `DEFERRED`, record the owner and next action, and continue every independent work item that remains valid.

Stop only for:

- an irreversible/destructive action requiring explicit human approval;
- a real-money/mainnet action requiring explicit human approval;
- missing credentials/accounts that cannot be created without the Principal;
- a governance decision reserved to the Principal;
- a fatal flaw requiring a strategic redesign decision;
- genuine inability to proceed without external evidence.

---

## 4. CRITICAL-PATH PRIORITY

The named ship-path milestone is **v1.6-verified x402 launch**.

No discretionary hardening gets critical-path priority while a named ship-path milestone can advance.

This includes, unless an executed ship-path test exposes the need:

- non-launch UI refinement;
- aesthetic redesign;
- provider expansion beyond launch need;
- low-value edge-case accumulation;
- documentation polish beyond required governance/evidence;
- speculative CI policy expansion;
- recovery micro-tests unrelated to the launch path;
- refactors performed only for style;
- feature expansion beyond the approved launch scope.

**Exception:** security fatal flaws, correctness defects, data/tenant-isolation defects, payment-integrity defects, runtime-identity defects, or other defects exposed by executed launch-path testing immediately become critical-path work.

---

## 5. EXECUTION SEQUENCE

Execute in this order unless live repository evidence proves a dependency-order correction is required.

### G0 — GOVERNANCE INSTALLATION + CANONICAL STATE RECONCILIATION

1. Verify live canonical repository and branch.
2. Verify live HEAD and inspect commits newer than the last recorded handoff.
3. Confirm RAPHAEL Master Spec v1.6 is presiding.
4. Install/verify RAPHAEL Security Governance Protocol in the canonical repo.
5. Create/update mandatory continuity artifacts:
   - `.build-state.json`
   - `docs/BUILD_HANDOFF.md`
   - `docs/SESSION_RECOVERY_PROTOCOL.md`
6. Create/update current one-block RAPHAEL MASTER TREE.
7. Create requirements traceability for this task.
8. Create/update risk register, decision log, interface map, and RED TEAM/failure-mode record at Critical Mission depth.
9. Record all tests as `PASSED`, `FAILED`, `BLOCKED`, `NOT RUN`, `DEFERRED`, `EXPIRED`, or `SUPERSEDED` — never inferred.

**G0 Exit:** a new authorized agent/operator can recover exact current build state and continue without chat-copy dependency.

---

### G1 — LAUNCH-SCOPE SECURITY HARDENING

Apply the RAPHAEL Security Governance Protocol to the exact x402 launch scope.

Mandatory launch-blocker closures:

1. Prevent service-level credential forwarding to arbitrary caller-controlled hosts.
2. Implement SSRF defenses:
   - HTTPS-only where required;
   - provider-host validation;
   - private/loopback/link-local/reserved network blocking;
   - cloud metadata blocking;
   - redirect validation;
   - DNS-rebinding protections where relevant.
3. Limit preview scope to public repositories until private-repository tenant authorization is verified.
4. Remove or production-gate legacy/demo/debug endpoints not required for the x402 launch.
5. Eliminate materially equivalent unpaid scanner bypass routes when commerce is enabled.
6. Restrict CORS appropriately for the commercial production surface.
7. Add request-size, scan-size, concurrency, timeout, and rate protections.
8. Run the production container as non-root and minimize runtime privilege.
9. Verify secret redaction from logs, telemetry, reports, errors, and evidence.
10. Add regression tests for each resolved security defect.
11. Run hostile/adversarial staging cases for launch-scope attack surfaces.

**G1 Exit:** Security Green for the exact limited x402 launch scope; unresolved critical/high practical vulnerabilities = none.

---

### G2 — X402 SHIP-PATH CONTRACT RECONCILIATION

Reconcile the current product catalog and actual deployed routes.

Verify the approved product ladder and machine contracts:

- preflight — free
- verify commit — paid
- safe-to-ship — paid
- repo scan — paid
- explain findings — paid
- attest — paid

Verify:

- product prices are sourced from the canonical product catalog;
- no stale single-price legacy environment contract controls the new commerce surface;
- unpaid requests produce expected x402 challenge behavior;
- invalid payment proof cannot reach fulfillment;
- settlement and fulfillment are bound to the purchased product;
- payment retry/idempotency behavior cannot double-charge or unsafely double-execute;
- mainnet remains interlocked until explicitly authorized.

**G2 Exit:** Engineering Green for the x402 commerce boundary.

---

### G3 — RAPHAEL v1.6 PRODUCTION REALIZATION DOMAINS 1–3

#### Domain 1 — Source + Traceability

- authoritative requirements mapped;
- approved release scope mapped;
- exact release candidate commit recorded;
- current decisions/risks/interfaces traceable;
- stale docs identified as legacy/superseded rather than silently relied upon.

#### Domain 2 — Build + Artifact Integrity

- release artifact uniquely identified;
- artifact tied to source commit;
- CI/build evidence tied to release candidate;
- dependency/build inputs recorded;
- authorized configuration class identified without secret values;
- release manifest generated;
- SBOM/provenance/signature or justified equivalent produced in proportion to Critical Mission exposure.

#### Domain 3 — Security + Supply Chain

- dependency vulnerability review;
- secret scanning;
- repository history secret review where practical;
- container/base-image review;
- credential/permission review;
- unresolved vulnerabilities formally dispositioned;
- security evidence tied to exact release candidate.

**G3 Exit:** Source/Traceability, Artifact, and Security evidence are current and release-bound.

---

### G4 — RAPHAEL v1.6 PRODUCTION REALIZATION DOMAINS 4–7

#### Domain 4 — Environment + Deployment

- target Railway environment mapped;
- domain/TLS/runtime/storage/network dependencies recorded;
- environment parity/differences documented;
- deployment source tied to authorized artifact/configuration;
- post-deployment health and mission-path verification executed.

#### Domain 5 — Data + State Continuity

- cache/telemetry persistence verified;
- backup/restore requirements defined;
- recovery/rollback or forward-recovery behavior verified where applicable;
- restart persistence tested;
- state corruption/failure boundaries documented at launch-relevant depth.

#### Domain 6 — Operational Readiness

- health/readiness/version identity;
- structured, secret-safe logs;
- metrics/alerts/owners;
- disablement/kill switch;
- operator runbook;
- safe restart;
- credential rotation procedure;
- incident escalation/recovery procedure.

#### Domain 7 — Performance + Reliability

Define and validate explicit budgets for:

- request latency;
- scan duration;
- concurrency;
- repository/file size;
- memory/CPU;
- provider timeout;
- retry behavior;
- rate limits;
- downstream failure;
- overload/resource exhaustion.

**G4 Exit:** Deployment Green + Operations Green prerequisites are met for the release candidate.

---

### G5 — LIVE BASE SEPOLIA ACCEPTANCE

Use the actual intended public/staging endpoint and approved test credentials/wallet configuration.

Required evidence:

1. exact deployed release identity verified;
2. unpaid paid-route request returns 402;
3. real Base Sepolia buyer payment settles;
4. purchased operation executes successfully;
5. first request evidence records expected non-cache path where applicable;
6. repeated same repo/SHA purchase demonstrates expected cache behavior;
7. transaction/settlement telemetry exists without secret material;
8. receipt/provenance/attestation output is independently retrievable where the current launch contract requires it;
9. failure/retry case does not produce unsafe double charge/execution;
10. current provider/credential posture is consistent with public-repo-only launch scope.

**G5 Exit:** x402 external dependency classification reaches at least `LIVE VERIFIED` for testnet and all launch-path evidence is current.

---

### G6 — REAL USER / EXTERNAL AGENT ACCEPTANCE

An intended external agent/consumer must complete the launch mission without undocumented developer intervention.

Required path:

```text
DISCOVER
  ↓
UNDERSTAND PRODUCT / PRICE
  ↓
PREFLIGHT IF NEEDED
  ↓
REQUEST PAID PRODUCT
  ↓
RECEIVE X402 CHALLENGE
  ↓
PAY
  ↓
RETRY / COMPLETE REQUEST
  ↓
RECEIVE CONTRACT-COMPLIANT RESULT
  ↓
VERIFY RESULT / RECEIPT / PROVENANCE AS APPLICABLE
```

Record:

- external agent identity/type where available;
- release/environment/configuration class;
- discovery mechanism;
- product purchased;
- settlement reference;
- operation result;
- limitations;
- evidence timestamp.

**G6 Exit:** User Acceptance Green for the approved x402 launch scope.

---

### G7 — v1.6 FINAL VERIFICATION + LIMITED LAUNCH AUTHORIZATION

Build the Production Realization Evidence Package required by RAPHAEL v1.6.

Must contain or reference:

- release manifest;
- authoritative source baseline;
- requirements traceability;
- artifact identity/provenance;
- dependency/security evidence;
- configuration provenance without secret values;
- environment/deployment topology;
- post-deployment verification;
- state/recovery evidence;
- observability/runbook;
- performance/reliability results;
- real-user/external-agent acceptance;
- external dependency classifications;
- evidence freshness ledger;
- waivers/accepted risks/deferred gates;
- RED TEAM disposition;
- Gate review;
- proposed production authorization record.

Report separately:

- Engineering Green
- Security Green
- Artifact Green
- Deployment Green
- Operations Green
- User Acceptance Green
- Production Authorized

**G7 Exit:** Gates 1–7 support launch; Gate 8 is presented to Principal for explicit authorization.

No tool/agent may self-authorize Gate 8.

---

### G8 — CONTINUOUS FULL-COMPLETION AFTER INITIAL X402 LAUNCH

After limited x402 launch authorization, do not stop.

Continue automatically through every remaining required 🟥 item from the canonical Master Tree, including where still applicable:

1. full canonical state/continuity completion;
2. governed policy engine;
3. Verification Receipt v1 with cryptographic signing and lineage;
4. agent/tool chain of custody;
5. governed learnings;
6. repository-to-runtime reconciliation;
7. full x402 production completion and durable receipt/payment evidence;
8. comprehensive integrated launch assurance;
9. monitoring/security alerting;
10. stale documentation reconciliation;
11. legacy-route/code removal;
12. private-repository/customer authorization architecture and tenant-isolation proof;
13. marketplace/discovery expansion after evidence supports it;
14. Base mainnet only after explicit Principal approval and current mainnet verification requirements are satisfied.

A red item may become `NOT APPLICABLE` only with recorded rationale and authority under RAPHAEL v1.6. It may not disappear silently.

---

## 6. BUILD-BATCH DISCIPLINE

For every meaningful build batch:

1. inspect live HEAD before editing;
2. identify impacted components and dependencies;
3. implement the smallest complete root-cause change;
4. add/update tests first where practical for defects/features;
5. run targeted validation;
6. run broader regression required by impact;
7. collect evidence;
8. commit/push approved source changes to the canonical branch/workflow;
9. update `.build-state.json`;
10. update `docs/BUILD_HANDOFF.md`;
11. update Master Tree statuses using evidence only;
12. set exact next work package;
13. continue automatically if executable.

Do not reopen completed work without evidence of a gap.

---

## 7. TEST / EVIDENCE TRUTH RULE

A control is not Green because implementation exists.

Use only:

- `PASSED`
- `FAILED`
- `BLOCKED`
- `NOT RUN`
- `DEFERRED`
- `EXPIRED`
- `SUPERSEDED`
- `NOT APPLICABLE`
- `WAIVED / RISK ACCEPTED`

Every Green claim must reference reproducible evidence tied to the relevant commit/artifact/environment.

Historical evidence must be revalidated when source, dependency, configuration, runtime, security exposure, payment path, user flow, or acceptance criteria materially changes.

---

## 8. SECURITY EXECUTION RULE

Security findings discovered on the launch path are repaired, not merely catalogued, when the agent is authorized and the repair is reversible and within task scope.

Required repair loop:

```text
DISCOVER
  ↓
VERIFY
  ↓
ROOT CAUSE
  ↓
TEST THAT EXPOSES DEFECT
  ↓
REPAIR
  ↓
TARGETED RETEST
  ↓
HOSTILE RETEST
  ↓
REGRESSION
  ↓
EVIDENCE
```

Never weaken a security control to obtain Green.

---

## 9. REAL-MONEY / MAINNET HOLD

Base mainnet and any real-money production-spend action remain explicitly human-gated.

Do not:

- switch to Base mainnet;
- spend real funds;
- enable unrestricted production payment exposure;
- rotate to a production private key;
- authorize production launch;

without explicit Principal approval after current evidence is presented.

---

## 10. DEFINITION OF DONE

This continuous build task is complete only when:

### Initial x402 release

- limited launch scope is explicit;
- v1.6 Domains 1–9 applicable to that scope are evidenced;
- Security Green is current;
- Artifact Green is current;
- Deployment Green is current;
- Operations Green is current;
- User Acceptance Green is current;
- Gates 1–7 are satisfied/dispositioned;
- Gate 8 is explicitly authorized by Principal.

### Full completion

- every required 🟥 Master Tree item has become 🟩, or is formally `NOT APPLICABLE`, `DEFERRED`, or externally `BLOCKED` with owner/evidence under v1.6;
- no stale legacy path can bypass the authorized product/security model;
- continuity artifacts are current;
- evidence is current and release-bound;
- the full product can be recovered and continued by a new authorized agent without prior-chat dependency.

---

## 11. START COMMAND FOR CODEX / CLAUDE / BUILD AGENT

Use this instruction verbatim:

> Recover RepoGuard from the live canonical repository and execute `docs/REPO_GUARD_CONTINUOUS_COMPLETION_BUILD_TASK.md` under RAPHAEL Master Spec v1.6. First reconcile the live HEAD against `.build-state.json` and `docs/BUILD_HANDOFF.md` if present. Install/verify v1.6 governance and the RAPHAEL Security Governance Protocol, establish/update the mandatory continuity artifacts, then advance the x402 critical path in the exact dependency order defined by this task. Repair launch-path security and correctness defects as they are verified. Do not give discretionary hardening critical-path priority while a named ship-path milestone can advance, except for defects exposed by executed ship-path/security tests. Mark external dependencies BLOCKED or DEFERRED without stopping independent work. After limited x402 launch readiness is achieved, continue automatically through all remaining required red-status items until the Master Tree is Green or each exception is formally governed. Never self-authorize Gate 8 or Base mainnet.