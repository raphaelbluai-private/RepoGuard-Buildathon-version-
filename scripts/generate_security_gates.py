#!/usr/bin/env python3
"""Generate exact-source RAPHAEL Security Gates 1-7 evidence."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "release-evidence"
sys.path.insert(0, str(ROOT / "backend"))

from security_gate_evidence import evaluate_gates


def main() -> None:
    source_sha = os.getenv("REPOGUARD_SOURCE_SHA") or os.getenv("GITHUB_SHA")
    if not source_sha:
        raise SystemExit("REPOGUARD_SOURCE_SHA/GITHUB_SHA is required")
    OUT.mkdir(parents=True, exist_ok=True)
    report = evaluate_gates(source_sha=source_sha, ci_run_id=os.getenv("GITHUB_RUN_ID"))
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    (OUT / "raphael-security-gates-1-7.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
