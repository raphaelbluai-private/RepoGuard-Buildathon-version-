"""Runtime identity and configuration reconciliation for RepoGuard."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Any

_SAFE_CONFIG_KEYS = (
    "REPOGUARD_X402_NETWORK",
    "REPOGUARD_X402_FACILITATOR_URL",
    "REPOGUARD_PUBLIC_PREVIEW_ONLY",
    "REPOGUARD_CACHE_TTL_SECONDS",
    "REPOGUARD_CACHE_MAX_ENTRIES",
    "REPOGUARD_MAX_REQUEST_BYTES",
    "REPOGUARD_MAX_CONCURRENT_SCANS",
)

_SECRET_MARKERS = ("TOKEN", "SECRET", "KEY", "PASSWORD", "PAY_TO", "CREDENTIAL")


@dataclass(frozen=True)
class RuntimeIdentity:
    source_commit: str | None
    deployment_id: str | None
    service_id: str | None
    image_digest: str | None
    config_hash: str
    identity_complete: bool


def _source_commit() -> str | None:
    value = (
        os.getenv("REPOGUARD_RELEASE_SHA")
        or os.getenv("RAILWAY_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
    )
    if not value or value.strip().lower() in {"unknown", "unset", "none"}:
        return None
    return value.strip()


def safe_configuration() -> dict[str, str]:
    config: dict[str, str] = {}
    for key in _SAFE_CONFIG_KEYS:
        value = os.getenv(key)
        if value is not None:
            config[key] = value
    return dict(sorted(config.items()))


def configuration_hash(config: dict[str, Any] | None = None) -> str:
    selected = safe_configuration() if config is None else config
    for key in selected:
        upper = key.upper()
        if any(marker in upper for marker in _SECRET_MARKERS):
            raise ValueError(f"Secret-like configuration key cannot be hashed into runtime identity: {key}")
    payload = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def runtime_identity() -> RuntimeIdentity:
    source_commit = _source_commit()
    deployment_id = os.getenv("RAILWAY_DEPLOYMENT_ID") or os.getenv("REPOGUARD_DEPLOYMENT_ID")
    service_id = os.getenv("RAILWAY_SERVICE_ID") or os.getenv("REPOGUARD_SERVICE_ID")
    image_digest = os.getenv("REPOGUARD_IMAGE_DIGEST")
    complete = bool(source_commit and (deployment_id or image_digest))
    return RuntimeIdentity(
        source_commit=source_commit,
        deployment_id=deployment_id,
        service_id=service_id,
        image_digest=image_digest,
        config_hash=configuration_hash(),
        identity_complete=complete,
    )


def runtime_identity_view() -> dict[str, Any]:
    return asdict(runtime_identity())


def require_runtime_identity() -> None:
    required = os.getenv("REPOGUARD_REQUIRE_RUNTIME_IDENTITY", "0").strip().lower() in {
        "1", "true", "yes", "on"
    }
    if required and not runtime_identity().identity_complete:
        raise RuntimeError(
            "Runtime identity is required but source commit plus deployment/image identity are unavailable."
        )


def public_runtime_identity_view() -> dict[str, Any]:
    identity = runtime_identity()
    return {
        "source_commit": identity.source_commit,
        "config_hash": identity.config_hash,
        "identity_complete": identity.identity_complete,
    }
