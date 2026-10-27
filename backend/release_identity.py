"""Deterministic, secret-free release identity and drift verification.

This module does not assert that a deployment is authorized. It produces an
identity contract that operators can reconcile with independently observed
runtime and image digests.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_SHA = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def release_manifest(*, source_sha: str, image_digest: str,
                     configuration: dict[str, Any], build_id: str,
                     sbom_digest: str | None = None) -> dict[str, Any]:
    if not _SHA.fullmatch(source_sha):
        raise ValueError("source_sha must be a full lowercase Git commit SHA")
    if not _DIGEST.fullmatch(image_digest):
        raise ValueError("image_digest must be a sha256 OCI image digest")
    if sbom_digest is not None and not _DIGEST.fullmatch(sbom_digest):
        raise ValueError("sbom_digest must be a sha256 digest")
    if not build_id.strip():
        raise ValueError("build_id required")
    # Only allow public, explicitly non-secret configuration keys.
    allowed = {"network", "public_preview", "scanner_version", "ruleset_version",
               "payment_enabled", "environment"}
    if set(configuration) - allowed:
        raise ValueError("Unapproved configuration key; secret material forbidden")
    identity = {
        "schema_version": "repoguard.release.v1",
        "source_sha": source_sha,
        "image_digest": image_digest,
        "sbom_digest": sbom_digest,
        "build_id": build_id,
        "configuration": configuration,
        "configuration_hash": canonical_hash(configuration),
    }
    return {**identity, "manifest_hash": canonical_hash(identity)}


def reconcile_runtime(manifest: dict[str, Any], *,
                      observed_source_sha: str | None,
                      observed_image_digest: str | None,
                      observed_configuration_hash: str | None) -> dict[str, Any]:
    expected = ("source_sha", "image_digest", "configuration_hash")
    observed = (observed_source_sha, observed_image_digest, observed_configuration_hash)
    mismatches = [key for key, value in zip(expected, observed)
                  if not value or value != manifest.get(key)]
    return {
        "status": "BLOCKED_UNKNOWN_OR_DRIFT" if mismatches else "IDENTITY_MATCH",
        "release_authorized": False,
        "mismatches": mismatches,
    }
