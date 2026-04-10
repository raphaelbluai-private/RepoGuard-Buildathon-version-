# RepoGuard — Stress & Abuse-Resilience Test Suite

> **⚠️  STAGING / LOCAL ONLY**
> Never point these tests at the production URL.
> The run script will refuse to run if the host looks like a public domain.

---

## What this tests

| Test type | Goal |
|-----------|------|
| **Baseline** | Establish p50/p95/p99 latency and throughput at 50 concurrent users |
| **Step load** | Find the user count at which latency degrades or error rates climb (10 → 200 users) |
| **Spike** | Verify graceful degradation under sudden burst traffic (10 → 250 → 10 users) |
| **Soak** | Detect memory leaks and latency drift over 10 minutes at steady load |
| **Abuse: brute-force login** | Confirm per-IP rate limit + per-email lockout fire on repeated wrong OTPs |
| **Abuse: OTP spam** | Confirm per-IP + per-email rate limits throttle flood of code-request calls |
| **Abuse: excessive pinging** | Confirm per-IP rate limit on `/api/repoguard/verify` throttles aggressive polling |

---

## Prerequisites

```bash
# 1. Backend must be running
cd backend && python run.py

# 2. Locust must be installed (already done in this environment)
pip install locust   # locust 2.x required

# 3. Make the runner executable
chmod +x stress_tests/run_tests.sh
```

---

## Quick start

```bash
# Run the full suite (all scenarios, ~20 minutes total)
./stress_tests/run_tests.sh

# Run a single scenario
./stress_tests/run_tests.sh --suite baseline
./stress_tests/run_tests.sh --suite step
./stress_tests/run_tests.sh --suite spike
./stress_tests/run_tests.sh --suite soak
./stress_tests/run_tests.sh --suite abuse_login
./stress_tests/run_tests.sh --suite abuse_otp
./stress_tests/run_tests.sh --suite abuse_polling

# Target a specific staging host
./stress_tests/run_tests.sh --host http://my-staging-server:8000
```

Results land in `stress_tests/results/`. Each scenario produces:
- `<scenario>_stats.csv` — per-endpoint aggregated latency + throughput
- `<scenario>_stats_history.csv` — time-series data for graphing
- `<scenario>.html` — Locust HTML report
- `<scenario>_rate_before.json` / `_rate_after.json` — rate-limit snapshots

---

## Generate the markdown report

```bash
python3 stress_tests/report.py \
    --results-dir stress_tests/results \
    --host http://localhost:8000
```

Output: `stress_tests/results/report.md`

---

## Running individual locust files manually

```bash
# Baseline — 50 users, 90 seconds
locust --locustfile stress_tests/locust/standard.py \
       --headless --host http://localhost:8000 \
       --users 50 --spawn-rate 10 --run-time 90s \
       --user-classes DashboardUser AuthFlowUser \
       --csv stress_tests/results/baseline

# Step load (shape controls users automatically)
locust --locustfile stress_tests/locust/step_load.py \
       --headless --host http://localhost:8000 \
       --users 200 --spawn-rate 50 --run-time 305s \
       --csv stress_tests/results/step_load

# Spike (shape controls users automatically)
locust --locustfile stress_tests/locust/spike.py \
       --headless --host http://localhost:8000 \
       --users 250 --spawn-rate 250 --run-time 125s \
       --csv stress_tests/results/spike

# Soak — 50 users, 10 minutes
locust --locustfile stress_tests/locust/standard.py \
       --headless --host http://localhost:8000 \
       --users 50 --spawn-rate 10 --run-time 600s \
       --user-classes DashboardUser AuthFlowUser \
       --csv stress_tests/results/soak

# Abuse: brute-force login
locust --locustfile stress_tests/locust/abuse.py \
       --headless --host http://localhost:8000 \
       --users 5 --spawn-rate 5 --run-time 60s \
       --user-classes BruteForceUser \
       --csv stress_tests/results/abuse_login

# Abuse: OTP spam
locust --locustfile stress_tests/locust/abuse.py \
       --headless --host http://localhost:8000 \
       --users 3 --spawn-rate 3 --run-time 60s \
       --user-classes OTPSpamUser \
       --csv stress_tests/results/abuse_otp

# Abuse: excessive pinging
locust --locustfile stress_tests/locust/abuse.py \
       --headless --host http://localhost:8000 \
       --users 5 --spawn-rate 5 --run-time 60s \
       --user-classes VerifyAbuseUser \
       --csv stress_tests/results/abuse_polling
```

---

## Rate-limit configuration (current)

| Endpoint | Limit | Window | Lockout on overflow |
|----------|-------|--------|---------------------|
| `POST /api/auth/request-code` per IP | 5 req | 60 s | 300 s |
| `POST /api/auth/request-code` per email | 3 req | 60 s | 300 s |
| `POST /api/auth/verify-code` per IP | 10 req | 60 s | 300 s |
| `POST /api/auth/verify-code` per email (failed only) | 5 failures | — | 300 s |
| `GET /api/repoguard/verify` per IP | 30 req | 60 s | 120 s |
| Polling endpoints (`/api/events` etc.) | none — infra layer | — | — |
| `GET /api/health` | none | — | — |

---

## File structure

```
stress_tests/
├── README.md                  ← you are here
├── run_tests.sh               ← orchestration script
├── report.py                  ← CSV → markdown report generator
├── results/                   ← created at runtime
│   ├── baseline_stats.csv
│   ├── step_load_stats.csv
│   ├── ...
│   └── report.md
└── locust/
    ├── standard.py            ← DashboardUser + AuthFlowUser (baseline/soak)
    ├── step_load.py           ← StepLoadShape + StepUser
    ├── spike.py               ← SpikeShape + SpikeUser
    └── abuse.py               ← BruteForceUser, OTPSpamUser, VerifyAbuseUser
```

---

## Captured metrics

- **p50 / p95 / p99 latency** — from Locust CSV stats
- **Throughput** (req/s) — from Locust CSV stats
- **Error rate** — from Locust CSV stats
- **Rate-limit trigger count** — from `/api/_internal/rate-stats` snapshots
- **Lockout trigger count** — from rate-stats before/after comparison
- **Memory / uptime** — from `/api/health` endpoint
- **CPU / process info** — visible in the backend workflow logs during test

---

## Security constraints

- Test target must be localhost or an internal IP (enforced by the runner script)
- No production credentials are used anywhere in the test suite
- All abuse tests use fake `@staging.test` email addresses
- `BruteForceUser` sends randomised wrong codes, never attempting real user accounts
- `/api/_internal/rate-stats` is for staging/diagnostics only — block it behind a router in production
