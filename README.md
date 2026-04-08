🛡️ RepoGuard
Stop insecure code before it reaches production.
🚀 Overview
RepoGuard is an enforcement-first security system that detects exposed secrets (like API keys), triggers automated remediation, and restores the system to a secure state—before code is merged.
This isn’t monitoring. This is enforcement.
⚡ Features
🔍 Secret detection (API keys, high-entropy tokens)
⚙️ Automated enforcement + remediation flow
🔄 Full lifecycle visibility:
Command → Breach → Correction → Resolution
🧠 Demo-safe architecture (no external APIs required)
🔐 Email + 2FA (demo mode)
🎛️ Settings (sound, haptics, light/dark mode)
📡 Live event feed# RepoGuard-Buildathon-version-
🧪 Demo Credentials
Plain text
Email: demo@repoguard.ai
Code: 123456
🖥️ Run in Codespaces
1. Start Backend
Bash
cd backend
pip install -r requirements.txt
python run.py
Runs on:

http://localhost:8000
2. Start Frontend
Bash
cd frontend
npm install
npm run dev
Runs on:

http://localhost:5173
🎬 Demo Flow
Open the app
Click “Simulate Breach”
Navigate through:

Command → Breach → Correction → Resolution
Watch:
live event feed
compliance improvement
system recovery
🧠 How It Works
Plain text
Detect → Enforce → Fix → Secure
Detects exposed secrets in code
Triggers enforcement automatically
Applies secure fix patterns
Restores system to compliant state
🏗️ Architecture

frontend/   → UI + demo experience
backend/    → API + detection + enforcement
deploy/     → cloud + CI/CD scaffolding
🔄 Modes
Mode
Behavior
demo
fully functional, no external APIs
production
activates real integrations
☁️ Production-Ready Path
RepoGuard is designed to scale into:
AWS (ECS, RDS, Redis)
Secrets Manager integration
Real API key revocation
CI/CD enforcement workflows
🏆 Why This Matters
Secrets leak.
Developers miss things.
Monitoring isn’t enough.
RepoGuard ensures:
Insecure code never makes it to production.
🔥 Final Note
This is a demo-enabled system backed by a production-grade architecture designed for real-world enforcement.
