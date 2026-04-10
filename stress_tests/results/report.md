# RepoGuard — Stress & Abuse Test Report

**Generated:** 2026-04-10 07:00:02
**Target host:** `http://localhost:8000` (staging only)

> ⚠️  This report was produced from staging/local tests only.
> Results reflect a single-process Python backend without a reverse proxy.

## Test Scenarios

## Baseline (50 users, 90 s)

**Overall health:** HEALTHY 🟢

| Metric | Value |
|--------|-------|
| Requests | 3,983 |
| Failures | 0 (0.0%) |
| Throughput | 44.7 req/s |
| p50 latency | 2 ms |
| p95 latency | 3 ms |
| p99 latency | 27 ms |

**Per-endpoint breakdown:**

| Endpoint | Requests | Errors | p50 | p95 | p99 | req/s |
|----------|----------|--------|-----|-----|-----|-------|
| `GET /api/events` | 1,433 | 0 (0.0%) | 2 ms | 3 ms | 25 ms | 16.1 |
| `GET /api/system-status` | 863 | 0 (0.0%) | 2 ms | 3 ms | 5 ms | 9.7 |
| `GET /api/repos` | 848 | 0 (0.0%) | 2 ms | 3 ms | 28 ms | 9.5 |
| `GET /api/compliance` | 536 | 0 (0.0%) | 2 ms | 4 ms | 27 ms | 6.0 |
| `GET /api/health` | 303 | 0 (0.0%) | 2 ms | 4 ms | 27 ms | 3.4 |

**Rate-limit telemetry:**

| Metric | Before | After |
|--------|--------|-------|
| Active lockouts | 2 | 2 |

Active lockout keys after test:
  - `otp_req:email:ratelimit-test@staging.test` — 89 s remaining
  - `otp_req:ip:127.0.0.1` — 89 s remaining


## Step Load (10→200 users, 5 min)

**Overall health:** HEALTHY 🟢

| Metric | Value |
|--------|-------|
| Requests | 4,644 |
| Failures | 0 (0.0%) |
| Throughput | 31.3 req/s |
| p50 latency | 2 ms |
| p95 latency | 4 ms |
| p99 latency | 19 ms |

**Per-endpoint breakdown:**

| Endpoint | Requests | Errors | p50 | p95 | p99 | req/s |
|----------|----------|--------|-----|-----|-----|-------|
| `GET /api/events` | 1,560 | 0 (0.0%) | 2 ms | 5 ms | 19 ms | 10.5 |
| `GET /api/system-status` | 926 | 0 (0.0%) | 2 ms | 4 ms | 15 ms | 6.2 |
| `GET /api/repos` | 925 | 0 (0.0%) | 2 ms | 4 ms | 21 ms | 6.2 |
| `GET /api/compliance` | 628 | 0 (0.0%) | 2 ms | 4 ms | 9 ms | 4.2 |
| `GET /api/health` | 306 | 0 (0.0%) | 2 ms | 5 ms | 21 ms | 2.1 |
| `GET /api/repoguard/verify` | 299 | 0 (0.0%) | 3 ms | 5 ms | 16 ms | 2.0 |


## Spike (10→250→10 users, 2 min)

_No data (test may not have run)._


## Soak (50 users, 10 min)

_No data (test may not have run)._


## Abuse — Brute-Force Login (60 s)

**Overall health:** HEALTHY 🟢

| Metric | Value |
|--------|-------|
| Requests | 5,409 |
| Failures | 0 (0.0%) |
| Throughput | 91.5 req/s |
| p50 latency | 4 ms |
| p95 latency | 6 ms |
| p99 latency | 9 ms |

**Per-endpoint breakdown:**

| Endpoint | Requests | Errors | p50 | p95 | p99 | req/s |
|----------|----------|--------|-----|-----|-----|-------|
| `POST /api/auth/verify-code [brute-force]` | 5,409 | 0 (0.0%) | 4 ms | 6 ms | 9 ms | 91.5 |

**Rate-limit telemetry:**

| Metric | Before | After |
|--------|--------|-------|
| Active lockouts | 0 | 2 |
| Emails with failed-verify counts | — | 1 |

Active lockout keys after test:
  - `auth_lock:victim@staging.test` — 240 s remaining
  - `auth_verify:ip:127.0.0.1` — 240 s remaining


## Abuse — OTP Spam (60 s)

**Overall health:** HEALTHY 🟢

| Metric | Value |
|--------|-------|
| Requests | 3,234 |
| Failures | 0 (0.0%) |
| Throughput | 54.8 req/s |
| p50 latency | 4 ms |
| p95 latency | 5 ms |
| p99 latency | 7 ms |

**Per-endpoint breakdown:**

| Endpoint | Requests | Errors | p50 | p95 | p99 | req/s |
|----------|----------|--------|-----|-----|-----|-------|
| `POST /api/auth/request-code [otp-spam]` | 3,234 | 0 (0.0%) | 4 ms | 5 ms | 7 ms | 54.8 |

**Rate-limit telemetry:**

| Metric | Before | After |
|--------|--------|-------|
| Active lockouts | 2 | 4 |
| Emails with failed-verify counts | — | 1 |

Active lockout keys after test:
  - `auth_lock:victim@staging.test` — 159 s remaining
  - `auth_verify:ip:127.0.0.1` — 159 s remaining
  - `otp_req:email:victim@staging.test` — 240 s remaining
  - `otp_req:ip:127.0.0.1` — 240 s remaining


## Abuse — Excessive Pinging (60 s)

**Overall health:** HEALTHY 🟢

| Metric | Value |
|--------|-------|
| Requests | 12,310 |
| Failures | 0 (0.0%) |
| Throughput | 208.3 req/s |
| p50 latency | 3 ms |
| p95 latency | 5 ms |
| p99 latency | 6 ms |

**Per-endpoint breakdown:**

| Endpoint | Requests | Errors | p50 | p95 | p99 | req/s |
|----------|----------|--------|-----|-----|-----|-------|
| `GET /api/repoguard/verify [ping-abuse]` | 12,310 | 0 (0.0%) | 3 ms | 5 ms | 6 ms | 208.3 |

**Rate-limit telemetry:**

| Metric | Before | After |
|--------|--------|-------|
| Active lockouts | 4 | 5 |
| Emails with failed-verify counts | — | 1 |

Active lockout keys after test:
  - `auth_lock:victim@staging.test` — 98 s remaining
  - `auth_verify:ip:127.0.0.1` — 98 s remaining
  - `otp_req:email:victim@staging.test` — 179 s remaining
  - `otp_req:ip:127.0.0.1` — 179 s remaining
  - `boot_verify:127.0.0.1` — 60 s remaining


## Key Findings

- Step-load completed with p95=4 ms and 0.0% errors — server handled the full ramp well.
- Brute-force login: rate limiting engaged correctly — 2 lockout key(s) active after test (`auth_lock:victim@staging.test`, `auth_verify:ip:127.0.0.1`). Attack traffic returned 429; locust counts these as success by design.
- OTP spam: email-flood protection engaged — 2 OTP lockout key(s) active after test (`otp_req:email:victim@staging.test`, `otp_req:ip:127.0.0.1`). Excess request-code calls returned 429.
- Excessive ping: boot-verify rate limit engaged — 1 lockout key(s) active after 12,310 pings (`boot_verify:127.0.0.1`). Polling endpoints (events, repos, compliance) are intentionally unthrottled at the app layer; throttle via reverse proxy in production.

## Hardening Recommendations

- **Auth endpoints**: Current limits (5 OTP/min/IP, 5 failed verifies → lockout) are good for a demo. For production, add CAPTCHA after 3 failures and server-side email verification flow.
- **Polling endpoints**: Not rate-limited at the app layer (by design). For production, place a reverse proxy (nginx / Cloudflare) in front with a per-IP request limit of ~300 req/min on `/api/*` paths.
- **Boot verify endpoint**: Per-IP limit of 30/min is appropriate. Consider lowering to 10/min and increasing lockout to 600 s for hardened deployments.
- **Memory**: `events` list is now capped at 100 items. For production, move to a database or message queue.
- **Observability**: Add structured logging (JSON) and export metrics to Prometheus / Grafana for continuous monitoring.

## Rate-Limit Configuration (as tested)

| Endpoint | Limit | Window | Lockout |
|----------|-------|--------|---------|
| `POST /api/auth/request-code` (per IP) | 5 req | 60 s | 300 s |
| `POST /api/auth/request-code` (per email) | 3 req | 60 s | 300 s |
| `POST /api/auth/verify-code` (per IP) | 10 req | 60 s | 300 s |
| `POST /api/auth/verify-code` (per email, failed only) | 5 failures | — | 300 s |
| `GET /api/repoguard/verify` (per IP) | 30 req | 60 s | 120 s |
| `GET /api/events` | none (infra layer) | — | — |
| `GET /api/repos` | none (infra layer) | — | — |
| `GET /api/compliance` | none (infra layer) | — | — |
| `GET /api/system-status` | none (infra layer) | — | — |
| `GET /api/health` | none | — | — |
