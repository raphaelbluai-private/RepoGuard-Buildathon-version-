# RepoGuard War Room

**A safety command layer for AI-built apps.**
Paste any public GitHub repo, get a Safe-to-Ship score in under a second — no login, no GitHub token, no AI in the loop.

> Built for the **Replit 10-Year Buildathon** on the `buildathon-war-room` branch.

---

## Why this exists

AI agents ship code fast. Most of what slips through isn't exotic — it's the boring stuff:
committed `.env` files, real keys in `.env.example`, missing build scripts, lockfiles
absent from version control, GitHub Actions with `permissions: write-all`, `eval()`
in production paths, `child_process.exec(userInput)`, `curl … | sh`, deploy configs
pointing at the wrong port.

RepoGuard runs deterministic checks against a public repo and renders a War Room view:
score, findings, before/after, fix plan, ship checklist, exportable report.

## Public scanner — what it does

Open the deployed app → paste a public GitHub repo URL or `owner/repo` → scan.

**Inputs accepted:**
- `owner/repo`
- `https://github.com/owner/repo`
- `https://github.com/owner/repo/tree/branch`

**Output (Safe-to-Ship Report):**
- Integrity score (0–100), projected score after fixes
- Status: `SHIP_BLOCKED` / `NEEDS_REVIEW` / `SAFE_TO_SHIP`
- Findings broken down by severity (critical / high / medium / low)
- 8-gate Safe-to-Ship Checklist
- Per-finding triage (Open / Needs Review / Resolved Manually / Accepted Risk)
- Deterministic Fix Plan
- Copy summary, Download JSON, Download CSV, Download Markdown report

**No private credentials required.** The scanner uses GitHub's unauthenticated public Contents API.

## The scan engine (12 deterministic checks)

| Check | What it catches |
|---|---|
| Committed `.env` | Real secrets in tracked dotenv files |
| `.env.example` real-secret detection | Templates that accidentally hold live values |
| Missing `.env.example` | Template absent → onboarding/security drift |
| Token regex sweep | AWS / GitHub / Stripe / OpenAI / generic high-entropy keys |
| `package.json` build/start | Missing or incorrect script targets |
| Lockfile present | `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock` |
| GitHub Actions permissions | `permissions: write-all` blanket grants |
| `.replit` deployment block | Port mismatch, missing run/build |
| `eval` / `exec` / `shell=True` | Dynamic code execution |
| `child_process.exec(userInput)` | Command injection paths |
| `curl … \| sh` / `wget … \| sh` | Untrusted code piped to shell |
| README presence | Bare-repo signal |

Severity weights: `critical=25 high=15 medium=8 low=3`. Score = `100 − Σ(weights)` clamped to `[0, 100]`.

Status thresholds: any critical or `score < 60` → `SHIP_BLOCKED`; any high or `score < 85` → `NEEDS_REVIEW`; otherwise `SAFE_TO_SHIP`.

## Stack

- **Frontend:** React 19 + Vite 6 + TypeScript, served from `artifacts/repoguard/`
- **Backend:** FastAPI on Python 3.11, in `backend/`
- **Monorepo:** pnpm workspaces
- **Scanner:** pure-Python, deterministic, parallelised over GitHub's public Contents API (`ThreadPoolExecutor` × 8 workers, 8s timeout per file)

## Run locally

```bash
# 1. Install deps
pnpm install
pip install -r backend/requirements.txt

# 2. Start the backend (FastAPI on :8000)
cd backend && python run.py

# 3. In a second terminal, start the frontend (Vite on :18733)
pnpm --filter @workspace/repoguard run dev
```

Open `http://localhost:18733/`. Vite proxies `/api/*` to `127.0.0.1:8000`.

**Public-by-default:** `/` lands directly in the public War Room — no boot animation, no login.

URL params:
- `/?repo=owner/repo` — auto-runs a live scan on load
- `/?sample=1` — loads the deterministic sample scan
- `/?auth=1` — opens the legacy operator AuthScreen (demo email + 2FA)

## Deploy on Replit

The project is pre-configured for autoscale deployment:

- **Build** (`artifact.toml` → `services.production.build`): builds the React frontend AND installs Python deps
  ```sh
  pnpm --filter @workspace/repoguard run build && pip install -r backend/requirements.txt
  ```
- **Run** (`artifact.toml` → `services.production.run`): starts the FastAPI backend, which serves both `dist/public/` (static frontend, SPA fallback to `index.html`) and `/api/*`
  ```sh
  cd backend && python run.py
  ```

Click **Publish** in the Replit workspace. The published app is reachable at the project's `.replit.app` domain. **No GitHub token, no environment secrets needed for public scans.**

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/scan` | Body `{repo: "owner/repo" \| URL}`. Rate limited 15/60s/IP. Always returns 200 with `{ok: true, ...}` or `{ok: false, error, message}` for `INVALID_INPUT` / `REPO_NOT_FOUND` / `RATE_LIMIT` / `NETWORK_ERROR` / `GITHUB_FORBIDDEN` / `BLOCKED` / `SCAN_ERROR`. Never crashes the request. |
| `GET` | `/api/repos`, `/api/events`, `/api/compliance`, `/api/system-status` | Live demo data for the legacy command/breach view |
| `POST` | `/api/auth/request-code`, `/api/auth/verify-code` | Demo-grade 2FA (codes returned in response, in-memory) |
| `POST` | `/api/demo-trigger`, `/api/demo-resolve` | Drive the breach → correction → resolution animation |

## Buildathon progress

| | Before | After |
|---|---|---|
| **Branch** | `buildathon-before` | `buildathon-war-room` |
| **What it was** | RepoGuard scanner/security concept — animated breach/2FA demo running on canned data | Public **War Room safety command layer** — real scans of real public repos, no login, deterministic engine, exportable report |
| **Audience** | Operator-only (login required) | Anyone with the URL |
| **Scan engine** | None (visual concept) | 12 deterministic checks, parallelised, sub-second on typical repos |
| **Output** | Animation only | Safe-to-Ship score + findings + 8-gate checklist + Fix Plan + JSON / CSV / Markdown export |
| **Deployment** | Frontend-only static serve | Single FastAPI process serving the built frontend + `/api/*` (autoscale-friendly) |

```text
                        ┌──────────────────────────┐
                        │  Public visitor (judge)  │
                        └─────────────┬────────────┘
                                      │  paste owner/repo
                                      ▼
                        ┌──────────────────────────┐
                        │   RepoGuard War Room UI  │
                        │   (React, no auth)       │
                        └─────────────┬────────────┘
                                      │  POST /api/scan
                                      ▼
                        ┌──────────────────────────┐
                        │    FastAPI scanner       │
                        │  ┌────────────────────┐  │
                        │  │ ThreadPoolExecutor │  │   GitHub public
                        │  │  ×8  (8s timeout)  │──┼──▶ Contents API
                        │  └────────────────────┘  │   (no token)
                        └─────────────┬────────────┘
                                      │  Safe-to-Ship score
                                      ▼
                        ┌──────────────────────────┐
                        │  Findings · Checklist    │
                        │  Fix Plan · Report       │
                        └──────────────────────────┘
```
