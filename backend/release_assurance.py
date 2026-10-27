"""Fail-closed release assurance for branch, repository, and signature governance."""
from __future__ import annotations

import os
import re
from typing import Any

_SHA = re.compile(r"^[0-9a-f]{40}$")


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def release_assurance(*, branch: str, source_sha: str, repository_visibility: str) -> dict[str, Any]:
    blockers: list[str] = []
    if branch != "x402-production":
        blockers.append("release_branch_not_canonical")
    if not _SHA.fullmatch(source_sha):
        blockers.append("source_sha_not_exact")
    if not _truthy("REPOGUARD_BRANCH_PROTECTION_VERIFIED"):
        blockers.append("branch_protection_unverified")
    if not _truthy("REPOGUARD_REQUIRED_CHECKS_VERIFIED"):
        blockers.append("required_checks_enforcement_unverified")
    if not _truthy("REPOGUARD_RELEASE_SIGNATURE_VERIFIED"):
        blockers.append("signed_release_process_unverified")
    if repository_visibility == "public" and not _truthy("REPOGUARD_PUBLIC_SOURCE_APPROVED"):
        blockers.append("public_source_disposition_unapproved")
    if repository_visibility not in {"public", "private", "internal"}:
        blockers.append("repository_visibility_unknown")

    return {
        "schema": "repoguard.release-assurance.v1",
        "branch": branch,
        "source_sha": source_sha,
        "repository_visibility": repository_visibility,
        "status": "ASSURED" if not blockers else "BLOCKED",
        "release_authorized": False,
        "blockers": blockers,
    }
