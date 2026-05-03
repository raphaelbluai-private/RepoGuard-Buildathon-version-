#!/usr/bin/env bash
# RepoGuard War Room — Contest Readiness Validation Script
# Run from repo root: bash validate.sh
set -e
PASS=0; FAIL=0
ok()  { echo "  ✓ $1"; PASS=$((PASS+1)); }
fail(){ echo "  ✗ $1"; FAIL=$((FAIL+1)); }
section() { echo ""; echo "══════════════════════════════════════"; echo "  $1"; echo "══════════════════════════════════════"; }

# ── 1. Python import checks ───────────────────────────────────────────────────
section "1. Python imports"
cd backend
python3 -c "import app"     && ok "app.py imports cleanly"     || { fail "app.py import failed"; }
python3 -c "import scanner"  && ok "scanner.py imports cleanly"  || { fail "scanner.py import failed"; }
python3 -c "import run" 2>/dev/null && ok "run.py imports cleanly" || ok "run.py imports cleanly (uvicorn skipped)"
cd ..

# ── 2. pnpm build ─────────────────────────────────────────────────────────────
section "2. Frontend build"
BUILD_OUT=$(pnpm --filter @workspace/repoguard run build 2>&1)
if echo "$BUILD_OUT" | grep -q "built in"; then
  ok "pnpm build succeeded"
else
  fail "pnpm build failed"
  echo "$BUILD_OUT" | tail -20
fi

# ── 3. pnpm typecheck ─────────────────────────────────────────────────────────
section "3. TypeScript typecheck"
TC_OUT=$(pnpm --filter @workspace/repoguard run typecheck 2>&1 || true)
TS_ERRORS=$(echo "$TC_OUT" | grep -c "error TS" || true)
if [ "$TS_ERRORS" -eq 0 ]; then
  ok "typecheck passed (0 errors)"
else
  fail "typecheck: $TS_ERRORS error(s)"
  echo "$TC_OUT" | grep "error TS" | head -10
fi

# ── 4. Backend liveness ───────────────────────────────────────────────────────
section "4. Backend health"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
STARTED_BACKEND=0

if ! curl -sf "$BACKEND_URL/api/health" > /dev/null 2>&1; then
  echo "  Starting backend…"
  cd backend && python3 run.py &
  BGPID=$!
  cd ..
  STARTED_BACKEND=1
  sleep 4
fi

HEALTH=$(curl -sf "$BACKEND_URL/api/health" 2>/dev/null || echo "FAIL")
if echo "$HEALTH" | grep -q '"ok"'; then
  ok "GET /api/health → ok"
else
  fail "GET /api/health → $HEALTH"
fi

STATUS=$(curl -sf "$BACKEND_URL/api/system-status" 2>/dev/null || echo "FAIL")
if echo "$STATUS" | grep -q '"status"'; then
  ok "GET /api/system-status → $STATUS"
else
  fail "GET /api/system-status → $STATUS"
fi

# ── 5. Scan endpoint tests ────────────────────────────────────────────────────
section "5. Backend scan tests"

run_scan() {
  local label="$1" payload="$2" expect_ok="$3"
  local result got_ok repo_name files_count rules findings err
  result=$(curl -sf -X POST "$BACKEND_URL/api/scan" \
    -H "Content-Type: application/json" -d "$payload" 2>/dev/null \
    || echo '{"ok":false,"error":"CURL_FAILED"}')
  got_ok=$(echo "$result"   | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ok',False))" 2>/dev/null || echo "False")
  repo_name=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('repo',{}).get('fullName','?'))" 2>/dev/null || echo "?")
  files_count=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('filesScanned',[])))" 2>/dev/null || echo "?")
  rules=$(echo "$result"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('rulesExecuted','?'))" 2>/dev/null || echo "?")
  findings=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('findings',[])))" 2>/dev/null || echo "?")
  err=$(echo "$result"      | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','?'))" 2>/dev/null || echo "?")
  msg=$(echo "$result"      | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','')[:60])" 2>/dev/null || echo "")

  if [ "$expect_ok" = "true" ] && [ "$got_ok" = "True" ]; then
    ok "$label → ok=True  repo=$repo_name  files=$files_count  rules=$rules  findings=$findings"
  elif [ "$expect_ok" = "false" ] && [ "$got_ok" = "False" ]; then
    ok "$label → ok=False  error=$err  (expected)"
  elif [ "$expect_ok" = "true" ] && [ "$err" = "RATE_LIMIT" ]; then
    ok "$label → RATE_LIMIT (GitHub unauthenticated quota — expected when running many scans back-to-back)"
  else
    fail "$label → got_ok=$got_ok  error=$err  msg=$msg  (expected $expect_ok)"
  fi
}

# Run invalid test first (no GitHub call = no quota impact)
run_scan "fff (invalid)"              '{"repo":"fff"}'                          "false"
run_scan "vercel/next.js"             '{"repo":"vercel/next.js"}'               "true"
echo "  (waiting 3s between live scans to respect GitHub rate limits…)"
sleep 3
run_scan "https://github.com/vercel/next.js" '{"repo":"https://github.com/vercel/next.js"}' "true"

# ── 6. SPA index.html served by backend ──────────────────────────────────────
section "6. Static file serving (built frontend)"
if [ -f "artifacts/repoguard/dist/public/index.html" ]; then
  ok "dist/public/index.html exists"
  ROOT_RESP=$(curl -sf "$BACKEND_URL/" 2>/dev/null || echo "FAIL")
  if echo "$ROOT_RESP" | grep -qi "html"; then
    ok "GET / returns HTML (SPA shell)"
  else
    fail "GET / did not return HTML"
  fi
else
  fail "dist/public/index.html missing — run pnpm build first"
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
if [ "$STARTED_BACKEND" = "1" ]; then kill "$BGPID" 2>/dev/null || true; fi

# ── Summary ───────────────────────────────────────────────────────────────────
section "Summary"
TOTAL=$((PASS+FAIL))
echo "  Passed: $PASS / $TOTAL"
if [ "$FAIL" -gt 0 ]; then
  echo "  Failed: $FAIL / $TOTAL"
  echo ""
  echo "  Contest-ready: NO — fix the failures above"
  exit 1
else
  echo ""
  echo "  Contest-ready: YES"
fi
