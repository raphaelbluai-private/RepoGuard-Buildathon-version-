"""
step_load.py — Stair-step load test.

Gradually ramps users from 10 → 25 → 50 → 100 → 200,
holding each level for 60 seconds to find the saturation point.

Run:
    locust --locustfile stress_tests/locust/step_load.py \
           --headless --host http://localhost:8000 \
           --csv results/step_load

Note: LoadTestShape controls user count; --users and --spawn-rate CLI
flags are ignored when a shape is present.
"""

import random
import string

from locust import HttpUser, task, between, LoadTestShape


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"step_{suffix}@staging.test"


class StepUser(HttpUser):
    """Mixed dashboard + occasional auth user for step-load testing."""
    wait_time = between(0.5, 1.0)

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
    def health(self):
        self.client.get("/api/health", name="GET /api/health")

    @task(1)
    def verify(self):
        with self.client.get(
            "/api/repoguard/verify",
            catch_response=True,
            name="GET /api/repoguard/verify",
        ) as r:
            if r.status_code == 429:
                r.success()   # Expected once rate limit is hit


class StepLoadShape(LoadTestShape):
    """
    Stair-step shape: 10 → 25 → 50 → 100 → 200 users.
    Each step is 60 seconds.  Total run time: 300 s (5 minutes).

    Purpose: identify the user count at which latency starts to degrade
    or error rates climb — that is the system's stable throughput ceiling.
    """
    stages = [
        {"duration":  60, "users":  10, "spawn_rate":   5},
        {"duration": 120, "users":  25, "spawn_rate":   8},
        {"duration": 180, "users":  50, "spawn_rate":  15},
        {"duration": 240, "users": 100, "spawn_rate":  25},
        {"duration": 300, "users": 200, "spawn_rate":  50},
    ]

    def tick(self):
        t = self.get_run_time()
        for stage in self.stages:
            if t < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None
