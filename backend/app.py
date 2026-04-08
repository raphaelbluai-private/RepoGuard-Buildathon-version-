from datetime import datetime
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

events = []
repos = [
    {
        "id": "1",
        "source": "GitHub",
        "name": "api-service",
        "issue": "No active issue",
        "severity": "none",
        "status": "secure",
        "before": 72,
        "after": 72,
        "checked": "now",
    },
    {
        "id": "2",
        "source": "GitLab",
        "name": "frontend",
        "issue": "No active issue",
        "severity": "none",
        "status": "secure",
        "before": 88,
        "after": 88,
        "checked": "now",
    },
    {
        "id": "3",
        "source": "Bitbucket",
        "name": "worker-queue",
        "issue": "No active issue",
        "severity": "none",
        "status": "secure",
        "before": 94,
        "after": 94,
        "checked": "now",
    },
]
system_status = {"status": "secure"}
login_codes: Dict[str, str] = {}

class EmailBody(BaseModel):
    email: str

class VerifyBody(BaseModel):
    email: str
    code: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def stamp(message: str):
    events.append({"message": message, "time": datetime.now().strftime("%H:%M:%S")})

def calculate_global_compliance():
    if not repos:
        return {"before": 100, "after": 100}
    before_avg = round(sum(repo["before"] for repo in repos) / len(repos))
    after_avg = round(sum(repo["after"] for repo in repos) / len(repos))
    return {"before": before_avg, "after": after_avg}

@app.get("/api/events")
def get_events():
    return events[-6:]

@app.get("/api/repos")
def get_repos():
    return repos

@app.get("/api/compliance")
def get_compliance():
    return calculate_global_compliance()

@app.get("/api/system-status")
def get_system_status():
    return system_status

@app.post("/api/auth/request-code")
def request_code(body: EmailBody):
    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    login_codes[body.email] = code
    return {"sent": True, "email": body.email, "demo_code": code}

@app.post("/api/auth/verify-code")
def verify_code(body: VerifyBody):
    verified = login_codes.get(body.email) == body.code
    return {"verified": verified}

@app.post("/api/demo-trigger")
def trigger():
    events.clear()
    system_status["status"] = "breach"

    repos[0]["issue"] = "Confirmed secret exposure"
    repos[0]["severity"] = "critical"
    repos[0]["status"] = "breach"
    repos[0]["before"] = 72
    repos[0]["after"] = 72
    repos[0]["checked"] = "now"

    repos[1]["issue"] = "Policy drift detected"
    repos[1]["severity"] = "warning"
    repos[1]["status"] = "warning"
    repos[1]["before"] = 88
    repos[1]["after"] = 88
    repos[1]["checked"] = "now"

    repos[2]["issue"] = "Minor config exposure"
    repos[2]["severity"] = "minor"
    repos[2]["status"] = "monitoring"
    repos[2]["before"] = 94
    repos[2]["after"] = 94
    repos[2]["checked"] = "now"

    stamp("Critical breach detected in GitHub / api-service")
    stamp("Policy drift detected in GitLab / frontend")
    stamp("Minor config exposure detected in Bitbucket / worker-queue")
    stamp("Enforcement triggered across all monitored sources")
    stamp("Secrets revoked, policies corrected, and checks enforced")
    stamp("All monitored sources returned to compliant state")

    for repo in repos:
        repo["status"] = "resolved"
        repo["issue"] = "Repository returned to compliance"
        repo["after"] = 100

    system_status["status"] = "resolved"

    return {"status": "ok"}
