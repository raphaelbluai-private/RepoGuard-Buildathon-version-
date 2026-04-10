"""
abuse.py — Abuse and brute-force resilience tests.

Three distinct user classes — run each separately using --user-classes:

  BruteForceUser   → repeated wrong OTP codes against one email
  OTPSpamUser      → flooding /api/auth/request-code for one email
  VerifyAbuseUser  → excessive pinging of /api/repoguard/verify

In all cases, receiving HTTP 429 is the DESIRED outcome and is recorded
as a success.  Any 5xx is a failure.  The goal is to verify that the
rate-limiting/lockout controls fire correctly and completely.

Run (one class at a time via --user-classes):
    locust --locustfile stress_tests/locust/abuse.py \
           --headless --host http://localhost:8000 \
           --users 5 --spawn-rate 5 --run-time 60s \
           --user-classes BruteForceUser \
           --csv results/abuse_login
"""

import random
from locust import HttpUser, task, constant

VICTIM_EMAIL = "victim@staging.test"


class BruteForceUser(HttpUser):
    """
    Simulates a brute-force attacker submitting random 6-digit codes
    as fast as possible for a fixed email address.

    Expected protection chain:
      1. Per-IP sliding window: 10 req / 60 s → HTTP 429 + 300 s lockout
      2. Per-email failed-attempt counter: 5 failures → HTTP 429 (account locked)

    Test is successful if both mechanisms trigger within the first ~60 s.
    """
    wait_time = constant(0.05)    # 20 req/s max per virtual user

    @task
    def brute_force_verify(self):
        code = str(random.randint(100000, 999999))
        with self.client.post(
            "/api/auth/verify-code",
            json={"email": VICTIM_EMAIL, "code": code},
            catch_response=True,
            name="POST /api/auth/verify-code [brute-force]",
        ) as r:
            if r.status_code == 429:
                r.success()       # Desired: rate-limit / lockout is working
            elif r.status_code == 200:
                body = r.json()
                if body.get("verified"):
                    r.failure("Correct code guessed — not a test error but unexpected")
                else:
                    r.success()   # Wrong code returned 200 (before lockout kicks in)
            else:
                r.failure(f"Unexpected HTTP {r.status_code}: {r.text[:80]}")


class OTPSpamUser(HttpUser):
    """
    Simulates an OTP-spam attacker hammering /api/auth/request-code
    for the same email to exhaust rate limits or reveal patterns.

    Expected protection chain:
      1. Per-IP: 5 req / 60 s → HTTP 429 + 300 s lockout
      2. Per-email: 3 req / 60 s → HTTP 429 + 300 s lockout (stricter)

    Test is successful if 429 responses appear within the first 5 requests.
    """
    wait_time = constant(0.05)

    @task
    def spam_otp_request(self):
        with self.client.post(
            "/api/auth/request-code",
            json={"email": VICTIM_EMAIL},
            catch_response=True,
            name="POST /api/auth/request-code [otp-spam]",
        ) as r:
            if r.status_code == 429:
                r.success()       # Desired
            elif r.status_code == 200:
                r.success()       # First few are expected to succeed
            else:
                r.failure(f"Unexpected HTTP {r.status_code}: {r.text[:80]}")


class VerifyAbuseUser(HttpUser):
    """
    Simulates a client hammering the boot-verification endpoint continuously
    (e.g. a bot polling it every 20 ms, far above any legitimate use).

    Expected protection chain:
      Per-IP: 30 req / 60 s → HTTP 429 + 120 s lockout

    With wait_time=0.02 s and 5 users, the group fires ~250 req/min,
    which is ~8x over the 30/min limit — lockout should trigger fast.
    Test is successful if 429 responses dominate after the first 30 requests.
    """
    wait_time = constant(0.02)    # 50 req/s per virtual user

    @task
    def ping_verify(self):
        with self.client.get(
            "/api/repoguard/verify",
            catch_response=True,
            name="GET /api/repoguard/verify [ping-abuse]",
        ) as r:
            if r.status_code == 429:
                r.success()       # Desired
            elif r.status_code == 200:
                r.success()       # First 30 are expected to succeed
            else:
                r.failure(f"Unexpected HTTP {r.status_code}: {r.text[:80]}")
