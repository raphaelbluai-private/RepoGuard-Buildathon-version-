# RepoGuard x402 Security Requirements Traceability

Baseline: `x402-production` at `62f1ee093749ebc9c3754c8eded556ff1c8419db`. Gate 8 remains **NOT AUTHORIZED**.

| Requirement | Control | Regression evidence | RAPHAEL state |
|---|---|---|---|
| Prevent SSRF and metadata access | `network_policy.validate_repository_destination`; HTTPS/provider host/443/DNS/public-IP enforcement; Git redirects disabled | `test_network_policy.py`, `test_source_adapters.py` | VERIFIED locally |
| Prevent credential exfiltration | Public Git environment removes RepoGuard secrets; commerce API rejects auth-required providers before network access | `test_public_scan_credentials.py`, `test_production_surface.py` | VERIFIED locally |
| Public repositories only | Credential-free head/clone; authenticated-only providers return `PUBLIC_REPOSITORY_REQUIRED` | `test_public_scan_credentials.py`, `test_production_surface.py` | VERIFIED locally |
| Remove privileged legacy surface | Production app no longer mounts `app.py`; explicit commerce routes and static-only fallback | `test_production_surface.py` | VERIFIED locally |
| Restrict browser access | Exact-origin CORS; wildcard configuration fails startup | `test_security_middleware.py` | VERIFIED locally |
| Bound abusive input/work | Body cap, direct-socket client quota, repository quota, nonblocking concurrency semaphore | `test_security_middleware.py` | VERIFIED locally |
| Preserve x402 payment boundary | Approved facilitator endpoints, malformed-payment denial, offline facilitator fixture, mainnet denial | `test_x402_payment_gate.py`, `test_x402_security.py` | VERIFIED locally; live settlement pending |
| Avoid payment-secret persistence | Telemetry accepts response metadata and stores only digest/safe settlement fields | `test_day3_discovery_telemetry.py` | VERIFIED locally |
| Least-privilege runtime | Non-root container user; dedicated data and temp paths | `test_deployment_security.py`; CI container build | CONTROLLED EVIDENCE PENDING until CI |
| Reproducible frontend | pnpm 9 pinned; only esbuild lifecycle script allowed; frozen lockfile | frontend typecheck/build; `test_deployment_security.py` | VERIFIED locally |
| Source lineage | Feature branch forked from exact `origin/x402-production` SHA; no merge from demo/main | Git merge-base/rev-list evidence in gate report | VERIFIED locally |
| Human launch authority | No deployment, real payment, visibility change, or mainnet activation performed | Gate report | BLOCKING for launch by design |

“VERIFIED locally” is not a claim about deployed controls. Branch protection, repository visibility, CI completion, live testnet settlement, runtime identity, and production telemetry require external evidence.
