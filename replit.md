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
- Live event feed
- Compliance score before/after display
- Repository status board
- Settings modal with: dark/light mode, sound on/off, haptics on/off

## API Endpoints

- `GET /api/repos` — repo list with status
- `GET /api/events` — recent events (last 8)
- `GET /api/compliance` — compliance score before/after
- `GET /api/system-status` — overall system status
- `POST /api/auth/request-code` — send 2FA code (returns demo_code in response)
- `POST /api/auth/verify-code` — verify 2FA code
- `POST /api/demo-trigger` — trigger the breach detection demo flow

## Notes

- Auth is demo-grade only (codes returned directly in API response for demo)
- Backend uses in-memory state (resets on restart)
- Frontend proxies `/api` calls to `http://127.0.0.1:8000`
