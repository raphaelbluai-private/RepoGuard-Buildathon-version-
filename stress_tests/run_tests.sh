#!/usr/bin/env bash
# ============================================================
#  RepoGuard — Staging-Only Stress & Abuse Test Runner
#  ============================================================
#  IMPORTANT: Run this ONLY against a local or staging instance.
#  Never point HOST at the production URL.
#
#  Usage:
#    chmod +x stress_tests/run_tests.sh
#    ./stress_tests/run_tests.sh [OPTIONS]
#
#  Options:
#    --host URL          Backend base URL  (default: http://localhost:$PORT or :8000)
#    --suite SUITE       One of: all baseline step spike soak abuse_login
#                                abuse_otp abuse_polling  (default: all)
#    --skip-report       Do not generate markdown report after tests
#    -h / --help         Show this message
#
#  Prerequisites:
#    pip install locust        (already done if you ran setup)
#    Backend must be running:  cd backend && python run.py
# ============================================================

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCUST_DIR="$SCRIPT_DIR/locust"
RESULTS_DIR="$SCRIPT_DIR/results"
HOST="${REPOGUARD_HOST:-http://localhost:${PORT:-8000}}"
SUITE="all"
SKIP_REPORT=false

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)        HOST="$2";        shift 2 ;;
    --suite)       SUITE="$2";       shift 2 ;;
    --skip-report) SKIP_REPORT=true; shift   ;;
    -h|--help)
      sed -n '/^#  Usage/,/^# ==/p' "$0" | head -20
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Safety checks ─────────────────────────────────────────────────────────────
if echo "$HOST" | grep -qiE '(replit\.app|replit\.dev|\.com|\.io|\.net)'; then
  echo "ERROR: HOST looks like a public/production URL: $HOST"
  echo "       This script is for STAGING/LOCAL only. Aborting."
  exit 1
fi

if ! command -v locust &>/dev/null; then
  echo "ERROR: locust not found. Run: pip install locust"
  exit 1
fi

mkdir -p "$RESULTS_DIR"

# ── Helper functions ──────────────────────────────────────────────────────────
log() { echo "[$(date '+%H:%M:%S')] $*"; }

wait_for_backend() {
  log "Checking backend at $HOST/api/health …"
  for i in $(seq 1 15); do
    if curl -sf "$HOST/api/health" >/dev/null 2>&1; then
      log "Backend is up."
      return 0
    fi
    sleep 1
  done
  echo "ERROR: Backend did not respond at $HOST/api/health after 15 s."
  echo "       Start it with:  cd backend && python run.py"
  exit 1
}

reset_rate_limits() {
  # Hit the backend to let lockout timers expire between abuse tests.
  log "Pausing 30 s to let rate-limit windows cool down …"
  sleep 30
}

run_locust() {
  local label="$1"
  local locustfile="$2"
  local users="$3"
  local spawn_rate="$4"
  local run_time="$5"
  shift 5
  local extra_args=("$@")

  log "──────────────────────────────────────────────"
  log "Starting: $label"
  log "  locustfile : $locustfile"
  log "  users      : $users"
  log "  spawn-rate : $spawn_rate"
  log "  run-time   : $run_time"
  log "  host       : $HOST"
  log "──────────────────────────────────────────────"

  # Snapshot rate-limit stats before the test
  curl -sf "$HOST/api/_internal/rate-stats" \
    > "$RESULTS_DIR/${label}_rate_before.json" 2>/dev/null || true

  locust \
    --locustfile "$locustfile" \
    --headless \
    --host "$HOST" \
    --users "$users" \
    --spawn-rate "$spawn_rate" \
    --run-time "$run_time" \
    --csv "$RESULTS_DIR/$label" \
    --html "$RESULTS_DIR/${label}.html" \
    --logfile "$RESULTS_DIR/${label}.log" \
    "${extra_args[@]}" \
    2>&1 | tee -a "$RESULTS_DIR/${label}_stdout.log" || true

  # Snapshot rate-limit stats after the test
  curl -sf "$HOST/api/_internal/rate-stats" \
    > "$RESULTS_DIR/${label}_rate_after.json" 2>/dev/null || true

  log "Completed: $label → $RESULTS_DIR/$label*"
}

# ── Individual test suite functions ───────────────────────────────────────────

run_baseline() {
  run_locust "baseline" \
    "$LOCUST_DIR/standard.py" \
    50 10 "90s" \
    DashboardUser AuthFlowUser
}

run_step_load() {
  # Shape controls users/spawn-rate; --users must still be set to the max
  run_locust "step_load" \
    "$LOCUST_DIR/step_load.py" \
    200 50 "305s"
}

run_spike() {
  run_locust "spike" \
    "$LOCUST_DIR/spike.py" \
    250 250 "125s"
}

run_soak() {
  log "Soak test: 50 users for 10 minutes"
  run_locust "soak" \
    "$LOCUST_DIR/standard.py" \
    50 10 "600s" \
    DashboardUser AuthFlowUser
}

run_abuse_login() {
  log "Abuse test: brute-force login (5 virtual attackers, 60 s)"
  run_locust "abuse_login" \
    "$LOCUST_DIR/abuse.py" \
    5 5 "60s" \
    BruteForceUser
}

run_abuse_otp() {
  log "Abuse test: OTP request flooding (3 attackers, 60 s)"
  run_locust "abuse_otp" \
    "$LOCUST_DIR/abuse.py" \
    3 3 "60s" \
    OTPSpamUser
}

run_abuse_polling() {
  log "Abuse test: excessive verify pinging (5 attackers, 60 s)"
  run_locust "abuse_polling" \
    "$LOCUST_DIR/abuse.py" \
    5 5 "60s" \
    VerifyAbuseUser
}

# ── Main ──────────────────────────────────────────────────────────────────────
wait_for_backend

START=$(date +%s)

case "$SUITE" in
  all)
    run_baseline
    sleep 5
    run_step_load
    sleep 5
    run_spike
    sleep 5
    run_soak
    reset_rate_limits
    run_abuse_login
    reset_rate_limits
    run_abuse_otp
    reset_rate_limits
    run_abuse_polling
    ;;
  baseline)      run_baseline       ;;
  step)          run_step_load      ;;
  spike)         run_spike          ;;
  soak)          run_soak           ;;
  abuse_login)   run_abuse_login    ;;
  abuse_otp)     run_abuse_otp      ;;
  abuse_polling) run_abuse_polling  ;;
  *)
    echo "Unknown suite: $SUITE"
    echo "Valid values: all baseline step spike soak abuse_login abuse_otp abuse_polling"
    exit 1
    ;;
esac

END=$(date +%s)
ELAPSED=$(( END - START ))

log "All tests finished in ${ELAPSED}s."

# ── Generate report ───────────────────────────────────────────────────────────
if [ "$SKIP_REPORT" = false ]; then
  if command -v python3 &>/dev/null; then
    log "Generating report …"
    python3 "$SCRIPT_DIR/report.py" --results-dir "$RESULTS_DIR" --host "$HOST"
    log "Report written to $RESULTS_DIR/report.md"
  else
    log "python3 not found — skipping report generation"
  fi
fi
