# RAPHAEL x402 Security Gate Report

Date: 2026-10-11 UTC<br>
Mission: harden the canonical RepoGuard x402 build for review<br>
Reconciled base: `origin/x402-production` at `976fb3d0fae2215feff5c4b20c7afb5d029769ad`
Work branch: `codex/x402-security-hardening-gate`

## Decision

Security implementation gates are **CONTROLLED EVIDENCE PENDING** until the pushed commit completes GitHub CI. Gate 8 is **NOT AUTHORIZED**. No deployment, real payment, mainnet enablement, production-data change, branch deletion, force push, or merge was performed.

## Implemented controls

- Fail-closed repository destination policy and DNS/IP classification.
- Credential-free, public-only commerce scans with auth-required providers rejected before network access.
- Removal of the mounted legacy/demo/auth/internal API from the production composition.
- Exact-origin CORS, security headers, request-size cap, client/repository quotas, and scan concurrency limit.
- Approved x402 facilitator host policy, Base mainnet denial, and hermetic payment challenge tests.
- Non-root container runtime and bounded writable paths.
- Pinned pnpm 9 and explicit esbuild-only lifecycle policy.

## Local evidence

Verified in the hardening workspace:

- `uv run python -m py_compile ...`: PASS.
- `PYTHONPATH=. uv run pytest -q tests`: PASS, 140 tests.
- `uv run ruff check --select E4,E7,E9,F ...`: PASS.
- `CI=1 corepack pnpm@9.15.9 install --frozen-lockfile`: PASS.
- pnpm 9 TypeScript check and Vite production build: PASS; 1,727 modules transformed.
- Current-tree and full-history filename-only pattern checks for private-key blocks and AWS access-key identifiers: zero matching files.
- Canonical governance copy SHA-256: `27fc46c54960744f0e5ae9c5fd965985b818876ca9566598e6cb60e5a4f1e179`, identical to the supplied source.
- `pip-audit` and `pnpm audit --audit-level high`: PASS; no known vulnerabilities found after dependency remediation.
- Docker build: CONTROLLED EVIDENCE PENDING; no Docker daemon was available locally.

## External evidence still required

- GitHub CI status for the final pushed commit.
- Docker image build result and immutable image digest (no local Docker daemon available during hardening).
- Repository visibility/private-access confirmation and branch protection/ruleset evidence from an authorized GitHub administrator.
- Live Base Sepolia payment challenge, settlement, replay/idempotency, and reconciliation evidence using approved test funds.
- Deployed runtime identity, egress control, managed rate limit, retention, alerting, backup/restore, and incident drill evidence.

These items must not be relabeled VERIFIED without source, date, scope, result, owner, and artifact location.
