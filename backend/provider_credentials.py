from __future__ import annotations

import os
from typing import Any

from source_adapters import normalize_provider_key, provider_capabilities


_CREDENTIAL_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "github": {
        "required": False,
        "environment_variables": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "alternatives": ["GITHUB_TOKEN", "GH_TOKEN"],
        "credential_type": "personal access token",
    },
    "gitlab": {
        "required": False,
        "environment_variables": ["REPOGUARD_GITLAB_TOKEN"],
        "alternatives": ["GITLAB_TOKEN"],
        "credential_type": "personal access token",
    },
    "bitbucket": {
        "required": False,
        "environment_variables": [
            "REPOGUARD_BITBUCKET_USERNAME",
            "REPOGUARD_BITBUCKET_APP_PASSWORD",
        ],
        "alternatives": ["REPOGUARD_BITBUCKET_TOKEN"],
        "credential_type": "username + app password/token",
    },
    "azure_devops": {
        "required": False,
        "environment_variables": ["REPOGUARD_AZURE_DEVOPS_PAT"],
        "alternatives": [],
        "credential_type": "personal access token",
    },
    "gitea": {
        "required": False,
        "environment_variables": ["REPOGUARD_GITEA_TOKEN"],
        "alternatives": ["REPOGUARD_GITEA_USERNAME"],
        "credential_type": "access token",
    },
    "gogs": {
        "required": False,
        "environment_variables": ["REPOGUARD_GOGS_TOKEN"],
        "alternatives": ["REPOGUARD_GOGS_USERNAME"],
        "credential_type": "access token",
    },
    "codeberg": {
        "required": False,
        "environment_variables": ["REPOGUARD_CODEBERG_TOKEN"],
        "alternatives": ["REPOGUARD_CODEBERG_USERNAME"],
        "credential_type": "access token",
    },
    "aws_codecommit": {
        "required": True,
        "environment_variables": [
            "REPOGUARD_AWS_CODECOMMIT_USERNAME",
            "REPOGUARD_AWS_CODECOMMIT_PASSWORD",
        ],
        "alternatives": [],
        "credential_type": "CodeCommit HTTPS Git credentials",
    },
    "google_cloud_source_repositories": {
        "required": True,
        "environment_variables": ["REPOGUARD_GCP_OAUTH_TOKEN"],
        "alternatives": [],
        "credential_type": "Google OAuth access token",
        "service_note": "Google Cloud Source Repositories is a legacy/end-of-sale service; compatibility is maintained for existing repositories.",
    },
    "sourcehut": {
        "required": False,
        "environment_variables": ["REPOGUARD_SOURCEHUT_TOKEN"],
        "alternatives": [],
        "credential_type": "access token",
    },
    "onedev": {
        "required": False,
        "environment_variables": ["REPOGUARD_ONEDEV_TOKEN"],
        "alternatives": ["REPOGUARD_ONEDEV_USERNAME"],
        "credential_type": "access token",
    },
    "sourceforge": {
        "required": False,
        "environment_variables": [],
        "alternatives": [],
        "credential_type": "public Git or provider-specific credentials",
    },
}


def provider_credential_requirements(provider: str) -> dict[str, Any]:
    key = normalize_provider_key(provider)
    if key not in provider_capabilities():
        raise ValueError(f"Unsupported provider: {provider}")
    requirements = dict(_CREDENTIAL_REQUIREMENTS.get(key, {}))
    requirements.setdefault("required", False)
    requirements.setdefault("environment_variables", [])
    requirements.setdefault("alternatives", [])
    return {"provider": key, **requirements}


def _all_required_present(requirements: dict[str, Any]) -> bool:
    names = list(requirements.get("environment_variables") or [])
    if not names:
        return False
    return all(bool(os.getenv(name)) for name in names)


def _any_credential_present(requirements: dict[str, Any]) -> bool:
    names = list(requirements.get("environment_variables") or [])
    alternatives = list(requirements.get("alternatives") or [])

    # Bitbucket token can replace the app-password half, but a username is still required.
    if requirements.get("provider") == "bitbucket":
        user = bool(os.getenv("REPOGUARD_BITBUCKET_USERNAME"))
        secret = bool(
            os.getenv("REPOGUARD_BITBUCKET_APP_PASSWORD")
            or os.getenv("REPOGUARD_BITBUCKET_TOKEN")
        )
        return user and secret

    if names and all(bool(os.getenv(name)) for name in names):
        return True
    return any(bool(os.getenv(name)) for name in alternatives)


def provider_connection_status(provider: str) -> dict[str, Any]:
    key = normalize_provider_key(provider)
    capabilities = provider_capabilities()
    if key not in capabilities:
        raise ValueError(f"Unsupported provider: {provider}")

    caps = dict(capabilities[key])
    req = provider_credential_requirements(key)
    required = bool(req.get("required"))
    configured = _all_required_present(req) if required else _any_credential_present(req)
    missing = [
        name for name in req.get("environment_variables", [])
        if not os.getenv(name)
    ] if required else []

    return {
        "provider": key,
        "adapter_status": caps.get("status"),
        "adapter_version": caps.get("adapter_version"),
        "public_scan_supported": bool(caps.get("public_scan")),
        "credentials_required": required,
        "credentials_configured": configured,
        "ready_for_public_scan": bool(caps.get("public_scan")) and caps.get("status") == "active",
        "ready_for_authenticated_scan": configured and caps.get("status") == "active",
        "missing_environment_variables": missing,
        "credential_type": req.get("credential_type"),
        "service_note": req.get("service_note"),
    }


def all_provider_connection_statuses() -> dict[str, dict[str, Any]]:
    return {
        provider: provider_connection_status(provider)
        for provider in provider_capabilities()
    }
