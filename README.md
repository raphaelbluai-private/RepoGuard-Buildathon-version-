# RepoGuard x402

RepoGuard is a deterministic pre-deployment assurance service for public source repositories. The production runtime exposes an x402-gated commerce API, creates commit-bound provenance, and deliberately excludes the legacy demo, OTP, operator, and free-scan routes.

## Canonical lineage

- Production development branch: `x402-production`
- Security hardening branch: `codex/x402-security-hardening-gate`
- Original hardening baseline: `62f1ee093749ebc9c3754c8eded556ff1c8419db`
- Reconciled review base: `976fb3d0fae2215feff5c4b20c7afb5d029769ad`
- Legacy branches (`demo`, `main`, and buildathon branches) are history/reference only and are not release sources.
- Gate 8 launch authority: **NOT AUTHORIZED**. Mainnet and deployment require a separate human decision.

## Security boundary

- Public repositories only; Git subprocesses do not receive provider tokens.
- HTTPS destinations are provider-host-bound, DNS checked, redirect-disabled, and rejected if they resolve to non-public space.
- Self-hosted Git hosts require `REPOGUARD_SELF_HOSTED_GIT_HOSTS`.
- Production exposes `/v1/health` and `/v1/repoguard/*`; `/api/*` legacy/demo/control routes are not mounted.
- Request bodies, per-client traffic, per-repository scans, and concurrent scans are bounded.
- CORS uses exact configured origins; wildcard origins are rejected.
- Base Sepolia is the default. Base mainnet fails closed without explicit release authority and an approved mainnet facilitator.
- The container runs as the unprivileged `repoguard` user.

See [RAPHAEL security governance](docs/security/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md), [requirements traceability](docs/security/SECURITY_REQUIREMENTS_TRACEABILITY.md), [security gate report](docs/security/RAPHAEL_X402_SECURITY_GATE_REPORT.md), and the [incident response runbook](docs/security/INCIDENT_RESPONSE_RUNBOOK.md).

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/health` | Non-secret service health |
| `GET` | `/v1/repoguard/products` | Product, price, and provider discovery |
| `POST` | `/v1/repoguard/preflight` | Public repository reachability |
| `POST` | `/v1/repoguard/verify` | Commit identity verification |
| `POST` | `/v1/repoguard/safe-to-ship` | Compact deterministic decision |
| `POST` | `/v1/repoguard/scan` | Full deterministic assessment |
| `POST` | `/v1/repoguard/explain` | Remediation-oriented view |
| `POST` | `/v1/repoguard/attest` | Provenance attestation view |

Paid POST routes are protected when `REPOGUARD_PAY_TO` is configured. Product prices are defined in `backend/product_catalog.py`.

## Local verification

Requires Python 3.11+, uv, Node 22, and pnpm 9.

```bash
uv sync --group dev
PYTHONPATH=backend uv run pytest -q backend/tests
uv run ruff check --select E4,E7,E9,F backend
CI=1 corepack pnpm@9.15.9 install --frozen-lockfile
corepack pnpm@9.15.9 --filter @workspace/repoguard run typecheck
corepack pnpm@9.15.9 --filter @workspace/repoguard run build
docker build -t repoguard:x402 .
```

Run the production composition:

```bash
cd backend
python run.py
```

The frontend build is served from `artifacts/repoguard/dist/public`. Configure production values from `backend/.env.production.example`; do not commit real secrets.

## Replit

Import this GitHub repository, select the `x402-production` branch (or the reviewed hardening PR branch while validating), and confirm `git rev-parse HEAD` matches the reviewed commit. Replit uses `backend/run.py`, which loads `commerce_app_v2:app`. Publishing, production secrets, and mainnet activation are intentionally outside automated authority.
