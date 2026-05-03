# REPOGUARD Workspace

## Overview

REPOGUARD is a full-stack security monitoring demo application. It features an animated breach-detection flow with email/2FA auth, live event feed, compliance scores, and a repository status board.

## Stack

### Frontend
- **Framework**: React 19 + Vite 6 (TypeScript)
- **Styles**: Inline styles + embedded CSS animations (no Tailwind)
- **Location**: `artifacts/repoguard/`
- **Port**: 18733 (served at `/`)

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Server**: Uvicorn
- **Location**: `backend/`
- **Port**: 8000 (in-memory state, demo-grade auth)

### Monorepo
- **Tool**: pnpm workspaces
- **Workspace file**: `pnpm-workspace.yaml`
- **Root package**: `package.json`

## Key Commands

- `pnpm install` — install all workspace dependencies
- `pnpm --filter @workspace/repoguard run dev` — run frontend dev server
- `cd backend && python run.py` — run FastAPI backend

## Workflows

- **REPOGUARD Backend** — FastAPI server on port 8000
- **artifacts/repoguard: web** — Vite dev server on port 18733

## Features

- Email login screen with 2FA demo verification
- Animated 4-stage breach detection demo (Command → Breach → Correction → Resolution)
- **War Room safety command layer** — public, real-repo scanner (Buildathon shipped feature)
  - **Public-by-default boot**: visiting `/` lands directly in the public War Room — no
    boot animation, no AuthScreen. `publicWarRoom` state defaults to `true`; only
    `/?auth=1` forces the legacy AuthScreen flow. Public mode shows a minimal shell
    with a "REPOGUARD · Public Scanner" top bar and a "Sign in →" escape hatch.
  - AuthScreen boot animation tightened from ~4350ms to ~900ms total (5 phases preserved,
    timers compressed). `/api/repoguard/verify` is fire-and-forget; nothing in the UI
    awaits it.
  - Hero header: "RepoGuard War Room / Agent-Built Safety Layer for AI Apps /
    Scan your project before you ship."
  - Repo input form: scans any public GitHub repo via unauthenticated GitHub Contents API (no token, no login)
  - Sample Scan fallback: deterministic seeded findings (5 risks, score 38 → 96) when GitHub is unreachable
  - Command Dashboard (status / integrity / risk mix / top blocker)
  - Before/After Integrity Score, Risk Detection Panel
  - What Broke / Why / How to Fix drill-down + deterministic Fix Plan Generator
  - **Per-finding triage statuses**: Open / Needs Review / Resolved Manually / Accepted Risk,
    user-settable in the drill-down (statusOverrides Record<string, RiskStatus> in WarRoom).
    Risk-card pill updates live; runtime-coerced via `coerceRiskStatus` so unknown values
    fall back to "open".
  - Safe-to-Ship Checklist (8 gates derived from real findings), Agent Build Trace timeline
  - Safe-to-Ship Report modal with Copy Summary / Download JSON / Download CSV exports
  - **Deep-link sharing**: `/?repo=owner/repo` auto-runs the scan on load; `/?sample=1`
    loads the seeded sample. StrictMode-guarded so the dev double-mount doesn't double-fire.
  - Backend scan engine: 12 deterministic checks (committed .env, token regexes, missing .env.example,
    real secrets in .env.example, package.json build/start, lockfile, workflow permissions,
    .replit deployment block, eval/exec/shell=True/child_process.exec/rm-rf//curl|sh/wget|sh, README)
- Live event feed
- Compliance score before/after display
- Repository status board
- Settings modal with: dark/light mode, sound on/off, haptics on/off

## War Room Implementation Notes

- New page registered as `"War Room"` in `pages` array (App.tsx); slot in `pageContent` map
- Frontend: `src/components/WarRoom.tsx` + types in `src/data/warRoomData.ts`
- Backend scanner: `backend/scanner.py` (pure deterministic, uses `requests` against GitHub public API)
- Endpoint: `POST /api/scan` with body `{repo: "owner/repo" | github URL}` — rate-limited 15/60s per IP
- Scanner uses `ThreadPoolExecutor(max_workers=8)` to fan out the ~25-30 GitHub Contents API
  fetches in parallel (was sequential). Per-request `TIMEOUT=8s` and the 10-workflow cap are
  preserved. Typical scan completes in ~0.9s vs. ~8-15s before. Rate-limit detection is
  thread-safe via a `"RATE_LIMIT"` sentinel returned from `_safe_fetch`.
- Frontend `handleRealScan` adds an `AbortController` watchdog (25s) so the UI can never get
  stuck in `scanMode.kind === "scanning"` even if the request hangs.
- Response: `{ok:true, repo, scanTime, filesScanned, findings, score, scoreProjected, status, gates}`
  or `{ok:false, error, message}`
- Severity weights: critical=25, high=15, medium=8, low=3 (max-cap 100, floor 0)
- Status: SHIP_BLOCKED if any critical or score<60; NEEDS_REVIEW if any high or score<85; else SAFE_TO_SHIP
- Sample Scan loads seeded data without making any network call (always available as fallback)
- Rest of app (Command/Breach/Correction/Resolution + scanner) is untouched

## API Endpoints

- `GET /api/repos` — repo list with status
- `GET /api/events` — recent events (last 8)
- `GET /api/compliance` — compliance score before/after
- `GET /api/system-status` — overall system status
- `POST /api/auth/request-code` — send 2FA code (returns demo_code in response)
- `POST /api/auth/verify-code` — verify 2FA code
- `POST /api/demo-trigger` — trigger the breach detection demo flow
- `POST /api/scan` — War Room real-repo scan; body `{repo}`; rate-limited 15/60s/IP

## Production deployment

- Single-process autoscale: FastAPI (`backend/app.py`) serves both the built React
  frontend (`artifacts/repoguard/dist/public`) AND `/api/*`. Vite is dev-only.
- Build: `pnpm --filter @workspace/repoguard run build && pip install -r backend/requirements.txt`
- Run: `cd backend && python run.py` — binds to `$PORT` (set to 18733 by `services.env`)
- SPA fallback in `app.py` resolves requested paths and enforces they stay inside
  `_DIST` via `.resolve()` + `.relative_to(_DIST)` to block path-traversal file disclosure;
  any escape attempt silently falls through to `index.html`.
- `/api/_internal/rate-stats` is 404'd in production unless `REPOGUARD_INTERNAL=1`
  is set (dev/CI only). It exposes limiter telemetry and must never be public.
- Production config lives in `artifacts/repoguard/.replit-artifact/artifact.toml`
  under `[services.production]` (build / run). The `.replit` `[deployment.run]` is
  ignored in the pnpm-workspace template.

## Notes

- Auth is demo-grade only (codes returned directly in API response for demo)
- Backend uses in-memory state (resets on restart)
- Frontend proxies `/api` calls to `http://127.0.0.1:8000` in dev only
- `normalize_repo()` in `backend/scanner.py` strips GitHub URL suffixes
  (`/tree/<branch>`, `/blob/<branch>/path`, `/pull/N`, `/issues/N`, `/actions`,
  `/wiki`, `/releases`, `/commits?`, `/compare`) before regex-matching, so a user
  pasting any GitHub deep-link still gets the right `owner/repo` parsed out.
