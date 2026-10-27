#!/usr/bin/env python3
"""Generate release-governance evidence without granting launch authorization."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "release-evidence"

import sys
sys.path.insert(0, str(ROOT / "backend"))
from release_assurance import release_assurance


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = release_assurance(
        branch=os.getenv("REPOGUARD_RELEASE_BRANCH", ""),
        source_sha=os.getenv("GITHUB_SHA", ""),
        repository_visibility=os.getenv("REPOGUARD_REPOSITORY_VISIBILITY", "unknown"),
    )
    (OUT / "release-assurance.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
