"""
spike.py — Sudden-spike load test.

Warms up at 10 users, instantly spikes to 250, then recovers.
Tests whether the server degrades gracefully under sudden burst traffic
and returns to normal latency after the spike subsides.

Run:
    locust --locustfile stress_tests/locust/spike.py \
           --headless --host http://localhost:8000 \
           --csv results/spike
"""

import random
import string

from locust import HttpUser, task, between, LoadTestShape


class SpikeUser(HttpUser):
    """Same mixed user as step load — shape controls the intensity."""
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
                r.success()


class SpikeShape(LoadTestShape):
    """
    Spike pattern:
      30 s  warm-up  @  10 users
      30 s  spike    @ 250 users  (instantaneous ramp)
      30 s  recovery @  10 users
      30 s  hold     @  10 users  (confirm return to baseline)

    Total: 120 s.

    A healthy server should:
      - Absorb the spike with acceptable latency degradation (< 3x baseline p95)
      - Return to near-baseline latency within 10-15 s of recovery
      - Produce zero 5xx errors (429s on verify are expected and acceptable)
    """
    stages = [
        {"duration":  30, "users":  10, "spawn_rate":   5},   # warm-up
        {"duration":  60, "users": 250, "spawn_rate": 250},   # spike (instant)
        {"duration":  90, "users":  10, "spawn_rate":  50},   # recovery
        {"duration": 120, "users":  10, "spawn_rate":   5},   # hold
    ]

    def tick(self):
        t = self.get_run_time()
        for stage in self.stages:
            if t < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None
