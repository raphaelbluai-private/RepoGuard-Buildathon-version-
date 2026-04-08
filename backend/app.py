from datetime import datetime
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

events = []
repos = [
    {"name": "api-service",  "issue": "No active issue", "status": "secure",  "checked": "now"},
    {"name": "frontend",     "issue": "No active issue", "status": "secure",  "checked": "now"},
    {"name": "worker-queue", "issue": "No active issue", "status": "secure",  "checked": "now"},
]
compliance = {"before": 72, "after": 72}
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

@app.get("/api/events")
def get_events():
    return events[-5:]

@app.get("/api/repos")
def get_repos():
    return repos

@app.get("/api/compliance")
def get_compliance():
    return compliance

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
    compliance["before"] = 72
    compliance["after"] = 72
    system_status["status"] = "breach"

    repos[0]["issue"] = "Exposed secret in PR diff"
    repos[0]["status"] = "breach"
    repos[0]["checked"] = "now"
    repos[1]["issue"] = "No active issue"
    repos[1]["status"] = "secure"
    repos[1]["checked"] = "now"
    repos[2]["issue"] = "No active issue"
    repos[2]["status"] = "secure"
    repos[2]["checked"] = "now"

    stamp("Breach detected in api-service")
    stamp("Enforcement triggered")
    stamp("Secret revoked")
    stamp("PR created and checks enforced")
    stamp("Repository secured")

    repos[0]["issue"] = "Patched via Secret Engine"
    repos[0]["status"] = "resolved"
    compliance["after"] = 100
    system_status["status"] = "resolved"

    return {"status": "ok"}
