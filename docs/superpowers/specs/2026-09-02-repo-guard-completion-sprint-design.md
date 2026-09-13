# REPO GUARD Completion Sprint — Governance and Architecture Design

**Status:** Design approved in chat; written-spec review pending  
**Mission weight:** Critical  
**Mission classification:** Yellow — Proceed With Controls  
**Canonical repository:** `raphaelbluai-private/RepoGuard-Buildathon-version-`  
**Active branch:** `x402-production`  
**Observed branch HEAD:** `fcc6b47c221d28c9d64b60eaf47a5a97c0f20098`  
**Governing authority:** RAPHAEL Master Spec v1.5, including RAPHAEL MASTER TREE v1.5.1, RED TEAM, 30/10 +300%, WAR ROOM, repository continuity, and ISO/IEC 42001-aligned controls  
**Owner and launch authority:** Principal  

## 1. Mission

Complete REPO GUARD as a production-grade, agent-purchasable repository verification service that produces deterministic findings and cryptographically verifiable evidence while distinguishing engineering success from production authorization.

The completion sprint closes the eight previously identified gaps without expanding into general code-review feature parity:

1. Canonical repository state and cross-session continuity.
2. Path-specific, versioned, hashed policy enforcement.
3. Signed Verification Receipt v1 with lineage.
4. Agent and tool chain of custody.
5. Governed learnings with evidence-backed supersession.
6. Repository-intent versus deployed-runtime reconciliation.
7. x402 production completion and purchase evidence.
8. Integrated launch assurance and evidence binder.

## 2. Controlling Principles

- The repository carries the build; conversation does not carry the build.
- Live branch state overrides stale summaries, screenshots, and prior status labels.
- Code existence is not proof of readiness.
- CI success is engineering evidence, not production authorization.
- Hashing proves integrity; signing proves attributable authenticity. REPO GUARD must not conflate them.
- Deterministic verdicts must remain separable from probabilistic explanations.
- Missing evidence, unknown runtime identity, invalid signatures, and unresolved policy conflicts fail closed.
- Material decisions remain human-authorized. REPO GUARD supplies evidence and enforcement outcomes; it does not authorize production launch autonomously.
- Stability exceeds speed; functionality exceeds aesthetics; completion exceeds expansion.
- Existing architecture is preserved unless a documented root-cause analysis proves a bounded replacement is necessary.

## 3. Scope Boundary

### In scope

- Backend policy, provenance, receipt, custody, runtime, storage, and x402 changes required by the eight work packages.
- API contracts required to create, verify, retrieve, compare, and purchase verification evidence.
- Schema migrations with rollback or forward-recovery procedures.
- Tests, fixtures, documentation, deployment configuration, operator runbooks, and evidence artifacts.
- Minimal frontend or CLI surfaces required to expose truthful status, human review, or receipt verification.

### Out of scope

- General-purpose AI pull-request review parity with CodeRabbit.
- Unrelated UI redesign, branding, analytics, collaboration, or marketplace features.
- New blockchains, payment assets, or pricing experiments beyond the approved x402/Base USDC path.
- Autonomous merge, deployment, remediation, or launch decisions.
- Refactoring unrelated modules merely to improve style.
- Claims of ISO/IEC 42001 certification or compliance.

An out-of-scope request enters the decision log and backlog. It cannot enter the active sprint without Principal-approved change control stating the displaced work, added risk, schedule effect, and validation impact.

## 4. Target Architecture

REPO GUARD will preserve deterministic scanning as the trusted core and add bounded services around it:

1. **Policy service** resolves repository and path policies into a canonical policy set.
2. **Verification orchestrator** binds repository snapshot, commit, policies, scanner version, and requested operation.
3. **Scanner adapters** produce deterministic findings and exact evidence locations.
4. **Custody recorder** records participating principals, agents, models, tools, versions, calls, and evidence hashes.
5. **Receipt service** canonicalizes results, links prior receipts, signs the receipt, and verifies signatures.
6. **Governed-learning service** preserves repository knowledge as immutable revisions with explicit current/superseded state and precedence.
7. **Runtime reconciler** compares repository intent with deployed identity and configuration evidence.
8. **Commerce and evidence store** binds x402 settlement, purchased operation, verification result, and receipt without storing secrets.

Every service exposes a narrow typed contract. The commercial API orchestrates services but does not reimplement their logic.

## 5. Canonical Data Contracts

### 5.1 Policy record

Each policy must contain a stable policy ID, schema version, policy revision, source, repository scope, path/glob scope, enforcement type, deterministic rule parameters, precedence, effective time, author or principal, status, canonical content hash, and supersession reference where applicable.

Resolution must be deterministic. Ambiguous equal-precedence conflicts block verification and name every conflicting policy.

### 5.2 Verification Receipt v1

The canonical machine-readable receipt must bind:

- Receipt ID, schema version, previous receipt ID/hash, creation time, and verification operation.
- Repository identity, provider, immutable commit SHA, canonical snapshot hash, and relevant deployment target.
- Scanner, adapter, ruleset, policy IDs, versions, and hashes.
- Requesting principal and available agent/model/tool identity with versions and invocation identifiers.
- Findings, deterministic verdict, evidence locations and hashes, limitations, and human-review status.
- Runtime reconciliation result when applicable.
- x402 network, asset, payer-safe identifier, receiver-safe identifier, transaction hash, settlement status, and purchased product.
- Canonical receipt hash, signature algorithm, key ID, signature, and verification instructions.

Private keys, access tokens, raw credentials, and unnecessary personal data must never enter the receipt.

### 5.3 Governed learning

Each learning is an append-only revision containing repository scope, path scope where relevant, source evidence, author/principal, confidence, effective time, precedence, state (`CURRENT`, `SUPERSEDED`, `HISTORY`, or disputed), and the record it supersedes. Deletion is tombstoning, not erasure of lineage.

### 5.4 Runtime evidence

Runtime evidence must identify environment, deployed artifact or image digest, source commit claim, configuration hash with secrets excluded, observation time, verifier, evidence source, and confidence/verification status. Unknown or unverifiable deployed identity cannot produce a passing reconciliation verdict.

## 6. Work Packages and Exit Gates

### WP0 — Canonical State and Continuity

Create and validate `.build-state.json`, `docs/BUILD_HANDOFF.md`, and `docs/SESSION_RECOVERY_PROTOCOL.md`. Reconstruct the RAPHAEL MASTER TREE v1.5.1 from the live branch, PRs, tests, deployment evidence, and governing documents.

**Exit:** A new authorized operator can recover exact branch, HEAD, last completed package, next package, deferred gates, and governing sources without chat-copy dependency.

### WP1 — Governed Policy Engine

Implement policy schemas, canonical hashing, path/glob resolution, precedence, conflicts, versioning, and repository configuration loading.

**Exit:** Repeated runs resolve identical policy sets and hashes; malformed, ambiguous, unsigned-if-required, or out-of-scope policies fail closed with actionable errors.

### WP2 — Verification Receipt v1

Implement canonical receipt serialization, previous-receipt lineage, signing, signature verification, key rotation metadata, and receipt retrieval.

**Exit:** Deterministic fixtures reproduce the same unsigned canonical payload; valid signatures verify; tampering, wrong keys, altered policies, commits, findings, or payment binding fail verification.

### WP3 — Agent and Tool Chain of Custody

Capture available principal, agent, model, tool/MCP, version, request, invocation, and evidence-hash data. Mark unavailable telemetry explicitly rather than inventing it.

**Exit:** Every material automated action has a traceable custody event or an explicit `UNAVAILABLE` marker with source and limitation.

### WP4 — Governed Learnings

Implement append-only repository learnings, precedence, source attribution, dispute state, supersession, and export.

**Exit:** No update destroys history; deterministic resolution identifies governing current records; conflicting or insufficiently sourced learnings cannot silently influence a verdict.

### WP5 — Repository-to-Runtime Reconciliation

Implement adapters and contracts that compare intended commit/configuration/artifact identity with observable deployed reality.

**Exit:** Matching evidence passes; drift, stale deployments, unverifiable identity, missing observations, and configuration mismatch produce explicit non-passing states with evidence.

### WP6 — x402 Production Completion

Wire durable commerce storage, receiver/network validation, settlement evidence, cache evidence, external-agent purchase flow, and purchased receipt retrieval.

**Exit:** A real approved Base Sepolia transaction demonstrates request, payment challenge, settlement, operation execution, persistence, cache behavior, receipt binding, and independent retrieval. Secrets and full sensitive payer data are absent from logs and receipts.

### WP7 — Integrated Launch Assurance

Run full regression, adversarial, security/privacy, migration, failure-recovery, API-contract, signature, payment, and deployment tests. Assemble the Evidence Binder and operator runbook.

**Exit:** RAPHAEL Gates 1–7 have objective evidence; all fatal flaws are resolved or formally accepted by authorized human decision; Gate 8 remains explicitly reserved for Principal launch authorization.

## 7. Sprint Guardrail Contract

The implementation will create `docs/REPO_GUARD_COMPLETION_SPRINT_GUARDRAILS.md` as a concise operator-enforced control document. It must contain:

- The immutable eight-package scope and explicit exclusions.
- Work-in-progress limit of one active work package, except independent verification activities.
- A requirement-to-code-to-test-to-evidence traceability rule.
- Entry and exit criteria for every package.
- Fatal-flaw stop conditions and escalation path.
- Change-control procedure and Principal approval boundary.
- Daily/batch continuity update requirement.
- Stagnation triggers and recovery actions.
- Definition of engineering Green versus production-authorized Green.
- Prohibition on placeholders, silent failures, unrecorded deferrals, and false PASS labels.

### Anti-sprawl rule

No task enters the sprint unless it closes a traced requirement, controls a registered risk, repairs a verified defect in the active path, or produces required validation evidence. Everything else is logged outside the sprint.

### Anti-stagnation rule

A package is stagnant when two consecutive implementation attempts fail without a new evidence-backed diagnosis, when the same defect is patched more than once, or when work remains blocked for one build batch without an owner and next action. Stagnation triggers root-cause review, interface re-evaluation, and a recorded decision to repair, redesign, defer with authority, or kill. Repeated blind patching is prohibited.

### Completion rule

No package is complete until implementation, tests, documentation, evidence, continuity updates, and applicable RED TEAM disposition are all present. Deferred runtime evidence is labeled `DEFERRED` or `BLOCKED`, never `PASS`.

## 8. Error and Failure Semantics

Use typed, machine-readable error codes with safe human explanations. Errors must identify the failed gate, responsible component, retryability, evidence reference, and corrective action without leaking secrets.

Required non-passing states include policy conflict, invalid input, repository access failure, incomplete snapshot, nondeterministic output, signature invalid, signing key unavailable, custody incomplete, runtime unknown, runtime drift, payment unsettled, persistence failure, governance review required, and launch not authorized.

Partial downstream failure must not overwrite a previously valid receipt or learning. Writes use transactions or idempotency controls where applicable. Retriable operations preserve correlation IDs and do not double-charge.

## 9. Security and Human Oversight

- Default deny for repository access, signing, receipt retrieval, runtime inspection, and privileged operations.
- Least-privilege, repository-scoped GitHub credentials.
- Signing keys stored through an approved secret or key-management mechanism; key material never committed.
- Input, path, glob, URL, provider, webhook, and schema validation at controlled interfaces.
- Redaction rules for logs, telemetry, receipts, and evidence exports.
- Human review status and limitations included wherever AI-assisted interpretation appears.
- AI output may explain findings or propose action, but cannot alter deterministic evidence, silently mutate policy, approve waivers, merge code, deploy, or authorize launch.

## 10. Testing and Evidence Strategy

Testing proceeds from contracts outward:

1. Schema and canonicalization unit tests.
2. Property and determinism tests across repeated runs.
3. Policy precedence and conflict fixtures.
4. Receipt signing, tampering, rotation, and lineage tests.
5. Custody completeness and unavailable-telemetry tests.
6. Governed-learning history and dispute tests.
7. Repository/runtime drift integration tests.
8. x402 idempotency, settlement, persistence, cache, and external-agent tests.
9. End-to-end API and deployment verification.
10. Regression, security/privacy, RED TEAM, recovery, and operator acceptance tests.

Every Green claim must cite a reproducible command or external evidence record, execution time, result, and relevant commit. Test fixtures are not represented as live-production evidence.

## 11. Requirements Traceability

The implementation plan will assign stable IDs beginning with `RG-CS-REQ-001`. Each requirement must map to its RAPHAEL or product source, strategic objective, risk controlled, implementation component, validation method, required evidence, owner, and status.

No requirement may be marked `VERIFIED` without evidence. Waived requirements require reason, risk acceptance, approver, expiration/review date, and effect on launch classification.

## 12. Launch and Kill Criteria

### Launch criteria

- All eight package exit gates satisfied or formally dispositioned.
- Full required test suite passes on the exact release commit.
- Production deployment identity matches the authorized commit/artifact.
- Signed receipts independently verify.
- Live x402 evidence is bound to the purchased operation and receipt.
- Durable storage, scoped credentials, receiver configuration, monitoring, recovery, and operator runbook are verified.
- RED TEAM findings are resolved or formally accepted.
- Evidence Binder is complete.
- Principal records Gate 8 launch authorization.

### Kill or redesign criteria

- Deterministic results cannot be reproduced.
- Cryptographic receipt authenticity cannot be safely implemented or operated.
- Payment can execute twice for one idempotent request or cannot be reconciled.
- Repository/runtime identity cannot be proven for the claimed verification product.
- Policy conflicts can silently change verdicts.
- Required credentials cannot be scoped adequately.
- The system requires hidden manual intervention to appear complete.
- Sprint expansion displaces critical controls without approved change control.

## 13. Design Decision

Adopt the gate-driven completion sprint. Do not use parallel feature tracks that permit partially integrated subsystems to accumulate, and do not use a monolithic hardening sprint that obscures evidence and continuation state. Execute WP0 through WP7 sequentially, allowing only independent validation to run concurrently.

The next step after written-spec approval is a file-by-file implementation plan under RAPHAEL v1.5. Code implementation begins only after that plan identifies dependencies, tests, migration order, validation commands, and continuity updates.
