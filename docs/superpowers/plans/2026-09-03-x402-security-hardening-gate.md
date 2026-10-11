# x402 Security Hardening Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the verified public-launch blockers on RepoGuard's canonical `x402-production` path without enabling mainnet, private-repository scanning, deployment, or human launch authorization.

**Architecture:** Put a fail-closed outbound repository policy in front of every Git operation, keep credentials bound to canonical provider hosts, and expose only an allowlisted production API/static surface. Add bounded request/concurrency controls and security headers around the commerce app, run the container as a non-root user, and emit exact-commit RAPHAEL evidence.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, x402 v2, Git subprocess adapters, pytest, Ruff, pnpm/Vite, Docker, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-02-repo-guard-completion-sprint-design.md` plus `docs/security/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md`

## Global Constraints

- Original work began on `x402-production` at `62f1ee0`; the completed change was reconciled onto `976fb3d` before review. Do not use `demo` or `main` as the implementation base.
- Public preview scans public repositories only; service-level credentials cannot be used for caller-selected private resources.
- HTTPS only; reject URL credentials, fragments, unsafe ports, provider/hostname mismatch, loopback/private/link-local/multicast/reserved destinations, and unapproved self-hosted providers.
- Keep Base mainnet disabled and do not perform a real payment or deployment without Principal approval.
- Preserve deterministic scanner behavior and the x402 paid route; legacy/demo/auth/control routes are not part of the production surface.
- No secret values in source, responses, logs, telemetry, tests, or evidence.
- RAPHAEL Gate 8 remains `NOT AUTHORIZED`.

---

### Task 1: Canonical outbound repository policy

**Files:**
- Create: `backend/network_policy.py`
- Modify: `backend/source_adapters.py`
- Test: `backend/tests/test_network_policy.py`
- Test: `backend/tests/test_source_adapters.py`

**Interfaces:**
- Produces: `validate_repository_destination(provider: str, url: str, *, resolver=socket.getaddrinfo) -> ValidatedDestination`
- Consumes: normalized provider key and generated clone URL.

- [ ] Write failing tests proving HTTP, embedded credentials, fragments, unsafe ports, provider-host mismatch, localhost, RFC1918, link-local metadata, reserved IPs, DNS resolution to private addresses, and unapproved self-hosted URLs fail closed.
- [ ] Run `PYTHONPATH=backend uv run pytest -q backend/tests/test_network_policy.py backend/tests/test_source_adapters.py` and confirm the new cases fail.
- [ ] Implement immutable canonical host/port policy, IP classification, injectable DNS resolution, and typed `UnsafeRepositoryDestination` errors.
- [ ] Call validation before `ls-remote` and clone; pass the validated URL into Git and attach credentials only after provider/host validation.
- [ ] Run the focused tests and confirm PASS.

### Task 2: Public-only repository authorization

**Files:**
- Modify: `backend/source_adapters.py`
- Modify: `backend/commerce_app_v2.py`
- Test: `backend/tests/test_public_scan_policy.py`

**Interfaces:**
- Produces: `PublicRepositoryRequired` and safe API error `PUBLIC_REPOSITORY_REQUIRED`.
- Consumes: provider capabilities and unauthenticated Git reachability.

- [ ] Write failing tests proving the public commerce path never injects configured provider credentials and auth-required providers are unavailable.
- [ ] Run focused tests and confirm RED.
- [ ] Add `access_mode="public"` to snapshot/head operations and make public mode use a credential-free Git environment.
- [ ] Reject auth-required/private-only provider requests before network work and map the result to safe 422/403 API errors.
- [ ] Run focused tests and confirm PASS.

### Task 3: Production surface isolation

**Files:**
- Create: `backend/production_surface.py`
- Modify: `backend/commerce_app_v2.py`
- Test: `backend/tests/test_production_surface.py`

**Interfaces:**
- Produces: middleware allowing `/v1/health`, `/v1/repoguard/*`, approved discovery, and static frontend GET/HEAD paths while returning 404 for legacy `/api/*`, auth, demo, and control endpoints.

- [ ] Write failing route-inventory tests proving `/api/scan`, OTP/demo/internal endpoints, and legacy x402 paths are inaccessible from the commerce app.
- [ ] Run focused tests and confirm RED.
- [ ] Add the explicit production allowlist, preserve SPA/static GET behavior, and prevent mounted legacy routes from expanding the API surface.
- [ ] Run focused tests and confirm PASS.

### Task 4: CORS, headers, body, concurrency, and quota controls

**Files:**
- Create: `backend/security_middleware.py`
- Modify: `backend/commerce_app_v2.py`
- Modify: `backend/.env.production.example`
- Test: `backend/tests/test_security_middleware.py`

**Interfaces:**
- Produces: `install_security_middleware(app)`, strict origin parsing, request-size cap, scan semaphore, per-client and per-repository quotas, safe headers.

- [ ] Write failing tests for denied unapproved origins, allowed configured origins, oversized bodies (413), concurrency exhaustion (429/503), repository quota exhaustion, spoofed-forwarding resistance, and required security headers.
- [ ] Run focused tests and confirm RED.
- [ ] Implement environment-bounded limits and strict CORS without wildcard origins, credentials, headers, or methods.
- [ ] Install middleware after routes are composed and document every environment setting.
- [ ] Run focused tests and confirm PASS.

### Task 5: x402 hermeticity and payment boundary regression

**Files:**
- Modify: `backend/x402_payments.py`
- Modify: `backend/tests/test_x402_payment_gate.py`
- Test: `backend/tests/test_x402_security.py`

**Interfaces:**
- Preserves: Base Sepolia `POST /v1/scan` challenge and mainnet deny-by-default.
- Produces: injectable facilitator/server construction for offline contract tests.

- [ ] Write failing tests for facilitator HTTPS host validation, payment-route binding, replay/idempotency metadata requirements, mainnet denial, and absence of raw payment signatures in telemetry.
- [ ] Replace import-time external initialization in tests with explicit injected fakes while leaving production x402 SDK middleware intact.
- [ ] Run all x402 and telemetry tests and confirm PASS without network access.

### Task 6: Container and supply-chain hardening

**Files:**
- Modify: `Dockerfile`
- Modify: `package.json`
- Modify: `.github/workflows/ci.yml`
- Create: `.github/dependabot.yml`
- Test: `backend/tests/test_deployment_security.py`

**Interfaces:**
- Produces: non-root runtime, constrained writable data/temp locations, deterministic pnpm 9 install policy, security scans and artifact evidence.

- [ ] Write static deployment tests proving a non-root `USER`, explicit data/temp directories, no wildcard runtime privilege, pinned pnpm major, and least-privilege workflow permissions.
- [ ] Run deployment tests and confirm RED.
- [ ] Harden the Docker runtime user and filesystem paths, add explicit `onlyBuiltDependencies: [esbuild]`, and extend CI with dependency/secret/static/container checks that do not expose secrets.
- [ ] Run deployment tests, frontend typecheck/build with pnpm 9, and Docker build if Docker is available.

### Task 7: Governance, traceability, and final evidence

**Files:**
- Create: `docs/security/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md`
- Create: `docs/security/RAPHAEL_X402_SECURITY_GATE_REPORT.md`
- Create: `docs/security/SECURITY_REQUIREMENTS_TRACEABILITY.md`
- Create: `docs/security/INCIDENT_RESPONSE_RUNBOOK.md`
- Modify: `README.md`
- Modify: `.build-state.json` if present, otherwise create it.

**Interfaces:**
- Produces: exact branch/commit security mission, RSGP requirement-to-control-to-test mapping, truthful Green/Yellow/Red status, and human-only Gate 8.

- [ ] Copy the supplied canonical governance protocol without weakening it.
- [ ] Document the public-only boundary, unavailable production/branch-protection evidence, remaining external controls, incident actions, and explicit `Gate 8: NOT AUTHORIZED`.
- [ ] Run secret scanning against current tree and Git history where tools are available; record tool/version/command and disposition without secret values.
- [ ] Run `python -m py_compile`, Ruff, full pytest, frontend typecheck/build, and container build/scans where available.
- [ ] Update evidence with the exact final commit and CI URL/status after publishing; never mark unavailable live controls VERIFIED.
- [ ] Commit, push without force, and open a PR targeting `x402-production`.
