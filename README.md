# RepoGuard

**Your API keys are already leaking.**

RepoGuard stops insecure code before it reaches production by detecting exposed secrets, blocking merges, and automatically fixing the issue.

## 10-second demo
Click "Simulate Breach" to see detection → enforcement → remediation → compliance restoration.

## Overview
RepoGuard is an enforcement-first security system that detects exposed secrets (like API keys), triggers automated remediation, and restores the system to a secure state—before code is merged. This isn't monitoring. This is enforcement.

## Features
- Secret detection (API keys, high-entropy tokens)
- Automated enforcement + remediation flow
- Full lifecycle visibility: Command → Breach → Correction → Resolution
- Demo-safe architecture (no external APIs required)
- Email + 2FA (demo mode)
- Settings (sound, haptics, light/dark mode)
- Live event feed

## Demo Credentials
```
Email: demo@repoguard.ai
Code:  shown on screen after clicking "Send code"
```

## Run Locally
**Backend**
```bash
cd backend
pip install -r requirements.txt
python run.py
# Runs on http://localhost:8000
```

**Frontend**
```bash
cd artifacts/repoguard
pnpm install
pnpm dev
# Runs on http://localhost:18733
```

## How It Works
```
Detect → Enforce → Fix → Secure
```
1. Detects exposed secrets in code
2. Triggers enforcement automatically
3. Applies secure fix patterns
4. Restores system to compliant state

## Architecture
```
artifacts/repoguard/   → React + Vite frontend
backend/               → FastAPI + enforcement logic
```

## Why This Matters
Secrets leak. Developers miss things. Monitoring isn't enough.
RepoGuard ensures insecure code never makes it to production.
