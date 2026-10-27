#!/usr/bin/env python3
"""Generate exact-SHA release evidence without embedding secrets."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "release-evidence"
TRACKED = [
    "Dockerfile",
    "railway.toml",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "pnpm-lock.yaml",
    "backend/commerce_app_v2.py",
    "backend/payment_operations.py",
    "backend/persistent_scan_cache.py",
    "backend/runtime_identity.py",
    "backend/product_catalog.py",
]


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    commit = os.getenv("REPOGUARD_SOURCE_SHA") or os.getenv("GITHUB_SHA") or git(["rev-parse", "HEAD"])
    branch = os.getenv("REPOGUARD_RELEASE_BRANCH") or os.getenv("GITHUB_REF_NAME") or git(["rev-parse", "--abbrev-ref", "HEAD"])
    files = {
        rel: sha256_file(ROOT / rel)
        for rel in TRACKED
        if (ROOT / rel).exists()
    }
    manifest = {
        "schema": "repoguard.release-manifest.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": "raphaelbluai-private/RepoGuard-Buildathon-version-",
        "branch": branch,
        "source_commit": commit,
        "tree": git(["rev-parse", f"{commit}^{{tree}}"]),
        "dirty": bool(git(["status", "--porcelain"])),
        "critical_file_hashes": files,
        "dependency_locks": {
            "python": sha256_file(ROOT / "uv.lock"),
            "node": sha256_file(ROOT / "pnpm-lock.yaml"),
        },
        "container": {
            "oci_revision_label_expected": commit,
            "image_digest": os.getenv("REPOGUARD_IMAGE_DIGEST"),
        },
        "runtime_identity_required_for_authorized_release": True,
    }
    (OUT / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
