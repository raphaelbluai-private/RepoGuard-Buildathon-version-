"""
standard.py — Realistic dashboard + auth user classes.

Used by:  baseline, soak, step-load, and spike tests
(step_load.py and spike.py import or redefine these user classes alongside
their LoadTestShape so each file stays self-contained for locust --locustfile.)
"""

import random
import string

from locust import HttpUser, task, between


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{suffix}@staging.test"


class DashboardUser(HttpUser):
    """
    Simulates an authenticated user polling the four live-data endpoints
    and occasionally hitting the boot-verify gate.

    Think: one browser tab, logged in, watching the dashboard in real time.
    Frontend polls every 1.2 s; we model that with wait_time 0.8–1.4 s and
    weighted tasks so the total request rate matches the real app.
    """
    wait_time = between(0.8, 1.4)

    @task(5)
    def poll_events(self):
        self.client.get("/api/events", name="GET /api/events")

    @task(3)
    def poll_repos(self):
        self.client.get("/api/repos", name="GET /api/repos")

    @task(3)
    def poll_status(self):
        self.client.get("/api/system-status", name="GET /api/system-status")

    @task(2)
    def poll_compliance(self):
        self.client.get("/api/compliance", name="GET /api/compliance")

    @task(1)
    def health_check(self):
        self.client.get("/api/health", name="GET /api/health")


class AuthFlowUser(HttpUser):
    """
    Simulates a new user going through the full auth flow:
    request a code → verify the code.

    Wait time is longer because auth flows happen infrequently compared
    to dashboard polling.
    """
    wait_time = between(4, 10)

    @task
    def complete_login(self):
        email = _random_email()

        with self.client.post(
            "/api/auth/request-code",
            json={"email": email},
            catch_response=True,
            name="POST /api/auth/request-code",
        ) as r:
            if r.status_code == 429:
                r.success()   # Rate limit is expected at high concurrency
                return
            if r.status_code != 200:
                r.failure(f"Unexpected {r.status_code}: {r.text[:120]}")
                return
            code = r.json().get("demo_code", "000000")

        self.client.post(
            "/api/auth/verify-code",
            json={"email": email, "code": code},
            name="POST /api/auth/verify-code",
        )

    @task(1)
    def boot_verify(self):
        self.client.get("/api/repoguard/verify", name="GET /api/repoguard/verify")
