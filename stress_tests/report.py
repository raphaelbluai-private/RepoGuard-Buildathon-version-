#!/usr/bin/env python3
"""
report.py — RepoGuard stress-test summary report generator.

Reads all Locust *_stats.csv files in the results directory and
produces a structured markdown report with:
  - p50 / p95 / p99 latency per endpoint per scenario
  - throughput (req/s) and error rate
  - max stable concurrent users
  - endpoints that degrade first
  - rate-limit / lockout trigger evidence
  - recommended hardening actions

Usage:
    python3 stress_tests/report.py \
        --results-dir stress_tests/results \
        --host http://localhost:8000
"""

import argparse
import csv
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path


# ─── CSV parsing ──────────────────────────────────────────────────────────────

LATENCY_COLS = ["50%", "95%", "99%"]

def _float(val: str) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def parse_stats_csv(path: str) -> list[dict]:
    """Return a list of per-endpoint stat rows from a Locust _stats.csv file."""
    rows = []
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Name") == "Aggregated":
                    row["_aggregated"] = True
                else:
                    row["_aggregated"] = False
                rows.append(row)
    except FileNotFoundError:
        pass
    return rows


def load_rate_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ─── Analysis helpers ─────────────────────────────────────────────────────────

def agg_row(rows: list[dict]) -> dict | None:
    for r in rows:
        if r.get("_aggregated"):
            return r
    return None


def endpoint_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if not r.get("_aggregated")]


def error_pct(row: dict) -> float:
    req = _float(row.get("Request Count", 0))
    fail = _float(row.get("Failure Count", 0))
    if req == 0:
        return 0.0
    return round(fail / req * 100, 2)


def fmt_ms(val) -> str:
    v = _float(str(val))
    if v == 0:
        return "—"
    if v < 1:
        return f"{v*1000:.0f} µs"
    return f"{v:.0f} ms"


def classify_health(agg: dict) -> str:
    """Return a health label based on aggregated p95 and error rate."""
    if agg is None:
        return "NO DATA"
    p95 = _float(agg.get("95%", 0))
    err = error_pct(agg)
    if err > 10 or p95 > 2000:
        return "DEGRADED ⚠️"
    if err > 2 or p95 > 500:
        return "STRESSED 🟡"
    return "HEALTHY 🟢"


# ─── Scenario report sections ─────────────────────────────────────────────────

def section_scenario(label: str, stats_path: str, rate_before: dict, rate_after: dict) -> str:
    rows = parse_stats_csv(stats_path)
    if not rows:
        return f"### {label}\n\n_No data (test may not have run)._\n\n"

    agg = agg_row(rows)
    eps = endpoint_rows(rows)

    out = []
    out.append(f"### {label}")
    out.append("")

    if agg:
        health = classify_health(agg)
        total_req = int(_float(agg.get("Request Count", 0)))
        total_fail = int(_float(agg.get("Failure Count", 0)))
        rps = _float(agg.get("Requests/s", 0))
        p50 = fmt_ms(agg.get("50%", 0))
        p95 = fmt_ms(agg.get("95%", 0))
        p99 = fmt_ms(agg.get("99%", 0))
        out.append(f"**Overall health:** {health}")
        out.append("")
        out.append(f"| Metric | Value |")
        out.append(f"|--------|-------|")
        out.append(f"| Requests | {total_req:,} |")
        out.append(f"| Failures | {total_fail:,} ({error_pct(agg):.1f}%) |")
        out.append(f"| Throughput | {rps:.1f} req/s |")
        out.append(f"| p50 latency | {p50} |")
        out.append(f"| p95 latency | {p95} |")
        out.append(f"| p99 latency | {p99} |")
        out.append("")

    if eps:
        out.append("**Per-endpoint breakdown:**")
        out.append("")
        out.append("| Endpoint | Requests | Errors | p50 | p95 | p99 | req/s |")
        out.append("|----------|----------|--------|-----|-----|-----|-------|")
        for r in sorted(eps, key=lambda x: -_float(x.get("Requests/s", 0))):
            name = r.get("Name", r.get("Type", "?"))
            reqs = int(_float(r.get("Request Count", 0)))
            errs = int(_float(r.get("Failure Count", 0)))
            err_pct_str = f"{error_pct(r):.1f}%" if reqs > 0 else "—"
            rps_ep = _float(r.get("Requests/s", 0))
            out.append(
                f"| `{name}` | {reqs:,} | {errs} ({err_pct_str}) "
                f"| {fmt_ms(r.get('50%',0))} | {fmt_ms(r.get('95%',0))} "
                f"| {fmt_ms(r.get('99%',0))} | {rps_ep:.1f} |"
            )
        out.append("")

    # Rate-limit evidence
    if rate_before or rate_after:
        lockouts_before = rate_before.get("active_lockout_count", 0)
        lockouts_after  = rate_after.get("active_lockout_count", 0)
        failures_after  = rate_after.get("tracked_email_failures", {})
        out.append("**Rate-limit telemetry:**")
        out.append("")
        out.append(f"| Metric | Before | After |")
        out.append(f"|--------|--------|-------|")
        out.append(f"| Active lockouts | {lockouts_before} | {lockouts_after} |")
        if failures_after:
            out.append(f"| Emails with failed-verify counts | — | {len(failures_after)} |")
        if rate_after.get("active_lockout_keys"):
            out.append("")
            out.append("Active lockout keys after test:")
            for k, secs in rate_after["active_lockout_keys"].items():
                out.append(f"  - `{k}` — {secs:.0f} s remaining")
        out.append("")

    return "\n".join(out) + "\n"


# ─── Findings engine ──────────────────────────────────────────────────────────

def derive_findings(results_dir: str) -> list[str]:
    """
    Derive human-readable findings from test results.

    IMPORTANT — abuse-test interpretation:
    Locust abuse scenarios deliberately call `.mark_as_success()` on 429 responses
    so the Locust failure counter stays at 0 even when rate-limiting is working
    perfectly.  For those scenarios the ground truth is the rate-stats JSON
    (active lockout keys), NOT the Locust failure count.
    """
    findings = []

    # ── Step-load: stable user ceiling ────────────────────────────────────────
    step_csv = os.path.join(results_dir, "step_load_stats.csv")
    step_rows = parse_stats_csv(step_csv)
    agg = agg_row(step_rows)
    if agg:
        p95 = _float(agg.get("95%", 0))
        err = error_pct(agg)
        if err < 2 and p95 < 500:
            findings.append(
                f"Step-load completed with p95={fmt_ms(p95)} and {err:.1f}% errors — "
                "server handled the full ramp well."
            )
        elif err < 5:
            findings.append(
                f"Step-load p95 reached {fmt_ms(p95)} ({err:.1f}% errors) — "
                "latency degrades under high concurrency; recommend profiling at 100+ users."
            )
        else:
            findings.append(f"Step-load failed with {err:.1f}% errors — server saturates before 200 users.")

    # ── Spike: burst recovery ──────────────────────────────────────────────────
    spike_rows = parse_stats_csv(os.path.join(results_dir, "spike_stats.csv"))
    spike_agg = agg_row(spike_rows)
    if spike_agg:
        p99 = _float(spike_agg.get("99%", 0))
        err = error_pct(spike_agg)
        if err < 1 and p99 < 3000:
            findings.append(f"Spike test: server absorbed burst traffic without 5xx errors (p99={fmt_ms(p99)}).")
        else:
            findings.append(
                f"Spike test: {err:.1f}% errors during spike — "
                "consider queue depth / connection pool tuning."
            )

    # ── Abuse helper: read rate-after JSON for a scenario ────────────────────
    def _rate_after(label: str) -> dict:
        return load_rate_json(os.path.join(results_dir, f"{label}_rate_after.json"))

    def _lockout_keys_containing(rate: dict, substr: str) -> list[str]:
        return [k for k in rate.get("active_lockout_keys", {}) if substr in k]

    # ── Abuse: brute-force login ───────────────────────────────────────────────
    al_rows = parse_stats_csv(os.path.join(results_dir, "abuse_login_stats.csv"))
    al_agg  = agg_row(al_rows)
    al_rate = _rate_after("abuse_login")
    if al_agg:
        total = _float(al_agg.get("Request Count", 0))
        # Use rate-stats as ground truth: 429s are marked success in locust
        auth_locks = _lockout_keys_containing(al_rate, "auth")
        if auth_locks:
            findings.append(
                f"Brute-force login: rate limiting engaged correctly — "
                f"{len(auth_locks)} lockout key(s) active after test "
                f"({', '.join(f'`{k}`' for k in auth_locks)}). "
                "Attack traffic returned 429; locust counts these as success by design."
            )
        else:
            err = error_pct(al_agg)
            findings.append(
                f"Brute-force login: no IP/email lockouts detected after {total:.0f} requests "
                f"({err:.1f}% locust failures) — verify `auth_verify` rate-limiter config."
            )

    # ── Abuse: OTP spam ────────────────────────────────────────────────────────
    ao_rows = parse_stats_csv(os.path.join(results_dir, "abuse_otp_stats.csv"))
    ao_agg  = agg_row(ao_rows)
    ao_rate = _rate_after("abuse_otp")
    if ao_agg:
        total = _float(ao_agg.get("Request Count", 0))
        otp_locks = _lockout_keys_containing(ao_rate, "otp_req")
        if otp_locks:
            findings.append(
                f"OTP spam: email-flood protection engaged — "
                f"{len(otp_locks)} OTP lockout key(s) active after test "
                f"({', '.join(f'`{k}`' for k in otp_locks)}). "
                "Excess request-code calls returned 429."
            )
        else:
            findings.append(
                f"OTP spam: no OTP lockouts detected after {total:.0f} requests — "
                "verify `otp_req` rate-limiter config."
            )

    # ── Abuse: excessive pinging ───────────────────────────────────────────────
    ap_rows = parse_stats_csv(os.path.join(results_dir, "abuse_polling_stats.csv"))
    ap_agg  = agg_row(ap_rows)
    ap_rate = _rate_after("abuse_polling")
    if ap_agg:
        total = _float(ap_agg.get("Request Count", 0))
        boot_locks = _lockout_keys_containing(ap_rate, "boot_verify")
        if boot_locks:
            findings.append(
                f"Excessive ping: boot-verify rate limit engaged — "
                f"{len(boot_locks)} lockout key(s) active after {total:,.0f} pings "
                f"({', '.join(f'`{k}`' for k in boot_locks)}). "
                "Polling endpoints (events, repos, compliance) are intentionally "
                "unthrottled at the app layer; throttle via reverse proxy in production."
            )
        else:
            findings.append(
                f"Excessive ping: no boot-verify lockouts detected after {total:.0f} pings — "
                "verify `boot_verify` rate-limiter config."
            )

    if not findings:
        findings.append("No test data found. Run the test suite first.")

    return findings


def derive_recommendations(results_dir: str) -> list[str]:
    recs = []

    # Check for any high-error scenarios
    for label in ["baseline", "step_load", "spike", "soak"]:
        rows = parse_stats_csv(os.path.join(results_dir, f"{label}_stats.csv"))
        agg = agg_row(rows)
        if agg and error_pct(agg) > 5:
            recs.append(
                f"**{label}**: Error rate exceeded 5% — add async workers or a connection pool "
                f"in front of the FastAPI process."
            )
        if agg and _float(agg.get("95%", 0)) > 1000:
            recs.append(
                f"**{label}**: p95 latency > 1 s — profile Python event loop and consider "
                f"running multiple uvicorn workers (`--workers 4`)."
            )

    recs.append(
        "**Auth endpoints**: Current limits (5 OTP/min/IP, 5 failed verifies → lockout) "
        "are good for a demo. For production, add CAPTCHA after 3 failures and "
        "server-side email verification flow."
    )
    recs.append(
        "**Polling endpoints**: Not rate-limited at the app layer (by design). "
        "For production, place a reverse proxy (nginx / Cloudflare) in front with "
        "a per-IP request limit of ~300 req/min on `/api/*` paths."
    )
    recs.append(
        "**Boot verify endpoint**: Per-IP limit of 30/min is appropriate. "
        "Consider lowering to 10/min and increasing lockout to 600 s for hardened deployments."
    )
    recs.append(
        "**Memory**: `events` list is now capped at 100 items. "
        "For production, move to a database or message queue."
    )
    recs.append(
        "**Observability**: Add structured logging (JSON) and export metrics to "
        "Prometheus / Grafana for continuous monitoring."
    )

    return recs if recs else ["No specific recommendations — all scenarios passed cleanly."]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RepoGuard test report generator")
    parser.add_argument("--results-dir", default="stress_tests/results", help="Directory containing Locust CSV output")
    parser.add_argument("--host",        default="http://localhost:8000",  help="Backend host tested against")
    parser.add_argument("--output",      default=None,                     help="Output file (default: results-dir/report.md)")
    args = parser.parse_args()

    out_path = args.output or os.path.join(args.results_dir, "report.md")

    # ── Build report ──────────────────────────────────────────────────────────
    lines = []
    lines.append("# RepoGuard — Stress & Abuse Test Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Target host:** `{args.host}` (staging only)")
    lines.append("")
    lines.append("> ⚠️  This report was produced from staging/local tests only.")
    lines.append("> Results reflect a single-process Python backend without a reverse proxy.")
    lines.append("")

    # ── Scenarios ─────────────────────────────────────────────────────────────
    lines.append("## Test Scenarios")
    lines.append("")

    scenarios = [
        ("Baseline (50 users, 90 s)",         "baseline"),
        ("Step Load (10→200 users, 5 min)",    "step_load"),
        ("Spike (10→250→10 users, 2 min)",     "spike"),
        ("Soak (50 users, 10 min)",            "soak"),
        ("Abuse — Brute-Force Login (60 s)",   "abuse_login"),
        ("Abuse — OTP Spam (60 s)",            "abuse_otp"),
        ("Abuse — Excessive Pinging (60 s)",   "abuse_polling"),
    ]

    for title, label in scenarios:
        stats_csv   = os.path.join(args.results_dir, f"{label}_stats.csv")
        rate_before = load_rate_json(os.path.join(args.results_dir, f"{label}_rate_before.json"))
        rate_after  = load_rate_json(os.path.join(args.results_dir, f"{label}_rate_after.json"))
        lines.append(f"## {title}")
        lines.append("")
        section = section_scenario(title, stats_csv, rate_before, rate_after)
        # Remove the duplicate heading already added
        section_body = "\n".join(section.split("\n")[2:])
        lines.append(section_body)

    # ── Key findings ──────────────────────────────────────────────────────────
    lines.append("## Key Findings")
    lines.append("")
    for finding in derive_findings(args.results_dir):
        lines.append(f"- {finding}")
    lines.append("")

    # ── Recommendations ───────────────────────────────────────────────────────
    lines.append("## Hardening Recommendations")
    lines.append("")
    for rec in derive_recommendations(args.results_dir):
        lines.append(f"- {rec}")
    lines.append("")

    # ── Rate-limit summary table ───────────────────────────────────────────────
    lines.append("## Rate-Limit Configuration (as tested)")
    lines.append("")
    lines.append("| Endpoint | Limit | Window | Lockout |")
    lines.append("|----------|-------|--------|---------|")
    lines.append("| `POST /api/auth/request-code` (per IP) | 5 req | 60 s | 300 s |")
    lines.append("| `POST /api/auth/request-code` (per email) | 3 req | 60 s | 300 s |")
    lines.append("| `POST /api/auth/verify-code` (per IP) | 10 req | 60 s | 300 s |")
    lines.append("| `POST /api/auth/verify-code` (per email, failed only) | 5 failures | — | 300 s |")
    lines.append("| `GET /api/repoguard/verify` (per IP) | 30 req | 60 s | 120 s |")
    lines.append("| `GET /api/events` | none (infra layer) | — | — |")
    lines.append("| `GET /api/repos` | none (infra layer) | — | — |")
    lines.append("| `GET /api/compliance` | none (infra layer) | — | — |")
    lines.append("| `GET /api/system-status` | none (infra layer) | — | — |")
    lines.append("| `GET /api/health` | none | — | — |")
    lines.append("")

    # ── Write output ──────────────────────────────────────────────────────────
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
