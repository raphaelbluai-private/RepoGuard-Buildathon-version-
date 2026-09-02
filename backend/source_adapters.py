from __future__ import annotations

import base64
import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class RepositoryRef:
    provider: str
    repository_id: str
    repository_url: str
    clone_url: str


_PROVIDER_CAPABILITIES: dict[str, dict[str, Any]] = {
    "github": {"status": "active", "adapter_version": "github-git-1.0.0", "public_scan": True, "auth_optional": True},
    "gitlab": {"status": "active", "adapter_version": "gitlab-git-1.0.0", "public_scan": True, "auth_optional": True},
    "bitbucket": {"status": "active", "adapter_version": "bitbucket-git-1.0.0", "public_scan": True, "auth_optional": True},
    "azure_devops": {"status": "active", "adapter_version": "azure-devops-git-1.0.0", "public_scan": True, "auth_optional": True},
    "gitea": {"status": "active", "adapter_version": "gitea-git-1.0.0", "public_scan": True, "requires_full_url": True, "auth_optional": True},
    "gogs": {"status": "active", "adapter_version": "gogs-git-1.0.0", "public_scan": True, "requires_full_url": True, "auth_optional": True},
    "codeberg": {"status": "active", "adapter_version": "codeberg-git-1.0.0", "public_scan": True, "auth_optional": True},
    "aws_codecommit": {"status": "active", "adapter_version": "aws-codecommit-git-1.0.0", "public_scan": False, "auth_required": True},
    "google_cloud_source_repositories": {"status": "active", "adapter_version": "gcp-csr-git-1.0.0", "public_scan": False, "auth_required": True, "service_state": "end_of_sale"},
    "sourcehut": {"status": "active", "adapter_version": "sourcehut-git-1.0.0", "public_scan": True, "auth_optional": True},
    "onedev": {"status": "active", "adapter_version": "onedev-git-1.0.0", "public_scan": True, "requires_full_url": True, "auth_optional": True},
    "sourceforge": {"status": "active", "adapter_version": "sourceforge-git-1.0.0", "public_scan": True, "auth_optional": True},
}

_ALIASES = {
    "azure": "azure_devops",
    "azure_repos": "azure_devops",
    "azuredevops": "azure_devops",
    "google_cloud_source_repository": "google_cloud_source_repositories",
    "google_cloud_source_repos": "google_cloud_source_repositories",
    "gcp_source_repositories": "google_cloud_source_repositories",
    "gcp_csr": "google_cloud_source_repositories",
    "source_hut": "sourcehut",
    "aws_code_commit": "aws_codecommit",
}

_PROVIDER_WORKFLOW_PATHS: dict[str, list[str]] = {
    "github": [".github/workflows"],
    "gitlab": [".gitlab-ci.yml"],
    "bitbucket": ["bitbucket-pipelines.yml"],
    "azure_devops": ["azure-pipelines.yml", ".azure-pipelines"],
    "gitea": [".gitea/workflows"],
    "gogs": [".gitea/workflows"],
    "codeberg": [".forgejo/workflows", ".gitea/workflows"],
    "aws_codecommit": ["buildspec.yml", "buildspec.yaml"],
    "google_cloud_source_repositories": ["cloudbuild.yaml", "cloudbuild.yml"],
    "sourcehut": [".builds"],
    "onedev": [".onedev-buildspec.yml", ".onedev-buildspec.yaml"],
    "sourceforge": [],
}


def normalize_provider_key(provider: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", (provider or "github").strip().lower()).strip("_")
    return _ALIASES.get(key, key)


def provider_capabilities() -> dict[str, dict[str, Any]]:
    return {k: dict(v) for k, v in _PROVIDER_CAPABILITIES.items()}


def adapter_version(provider: str) -> str:
    key = normalize_provider_key(provider)
    if key not in _PROVIDER_CAPABILITIES:
        raise ValueError(f"Unsupported provider: {provider}")
    return str(_PROVIDER_CAPABILITIES[key]["adapter_version"])


def _strip_git_suffix(value: str) -> str:
    return value[:-4] if value.endswith(".git") else value


def _id_from_url(url: str) -> str:
    p = urlparse(url)
    path = p.path.strip("/")
    if "/_git/" in path:
        org_project, repo = path.split("/_git/", 1)
        return f"{org_project}/{_strip_git_suffix(repo)}"
    if path.startswith("p/") and p.netloc == "git.code.sf.net":
        return path[2:]
    if path.startswith("v1/repos/") and "git-codecommit." in p.netloc:
        region = p.netloc.split("git-codecommit.", 1)[1].split(".amazonaws.com", 1)[0]
        return f"{region}/{path.split('/', 2)[2]}"
    if path.startswith("p/") and p.netloc == "source.developers.google.com":
        m = re.match(r"p/([^/]+)/r/(.+)$", path)
        if m:
            return f"{m.group(1)}/{_strip_git_suffix(m.group(2))}"
    parts = path.split("/")
    if p.netloc == "git.sr.ht" and len(parts) >= 2:
        return f"{parts[-2].lstrip('~')}/{_strip_git_suffix(parts[-1])}"
    if len(parts) >= 2:
        return f"{parts[-2]}/{_strip_git_suffix(parts[-1])}"
    return _strip_git_suffix(path)


def build_clone_url(provider: str, repo_input: str) -> RepositoryRef:
    key = normalize_provider_key(provider)
    if key not in _PROVIDER_CAPABILITIES:
        raise ValueError(f"Unsupported provider: {provider}")

    raw = (repo_input or "").strip().rstrip("/")
    if not raw:
        raise ValueError("Repository is required")

    if raw.startswith(("https://", "http://")):
        clone_url = raw
        repo_id = _id_from_url(clone_url)
        return RepositoryRef(key, repo_id, _strip_git_suffix(clone_url), clone_url)

    raw = raw.removesuffix(".git").strip("/")
    if key == "github":
        clone_url = f"https://github.com/{raw}.git"
    elif key == "gitlab":
        clone_url = f"https://gitlab.com/{raw}.git"
    elif key == "bitbucket":
        clone_url = f"https://bitbucket.org/{raw}.git"
    elif key == "codeberg":
        clone_url = f"https://codeberg.org/{raw}.git"
    elif key == "azure_devops":
        parts = raw.split("/")
        if len(parts) != 3:
            raise ValueError("Azure DevOps shorthand must be org/project/repo or a full clone URL")
        clone_url = f"https://dev.azure.com/{parts[0]}/{parts[1]}/_git/{parts[2]}"
    elif key == "sourcehut":
        parts = raw.split("/", 1)
        if len(parts) != 2:
            raise ValueError("SourceHut shorthand must be user/repo or a full clone URL")
        clone_url = f"https://git.sr.ht/~{parts[0].lstrip('~')}/{parts[1]}"
    elif key == "sourceforge":
        parts = raw.split("/", 1)
        if len(parts) != 2:
            raise ValueError("SourceForge shorthand must be project/repo or a full clone URL")
        clone_url = f"https://git.code.sf.net/p/{parts[0]}/{parts[1]}"
    elif key == "aws_codecommit":
        parts = raw.split("/", 1)
        if len(parts) != 2:
            raise ValueError("AWS CodeCommit shorthand must be region/repo or a full clone URL")
        clone_url = f"https://git-codecommit.{parts[0]}.amazonaws.com/v1/repos/{parts[1]}"
    elif key == "google_cloud_source_repositories":
        parts = raw.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Google Cloud Source Repositories shorthand must be project/repo or a full clone URL")
        clone_url = f"https://source.developers.google.com/p/{parts[0]}/r/{parts[1]}"
    elif key in {"gitea", "gogs", "onedev"}:
        raise ValueError(f"{key} is self-hostable; provide the full HTTPS clone URL")
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return RepositoryRef(key, raw, _strip_git_suffix(clone_url), clone_url)


def _basic_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Authorization: Basic {token}"


def _auth_header(provider: str) -> str | None:
    key = normalize_provider_key(provider)
    if key == "github":
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        return _basic_header("x-access-token", token) if token else None
    if key == "gitlab":
        token = os.getenv("REPOGUARD_GITLAB_TOKEN") or os.getenv("GITLAB_TOKEN")
        return _basic_header("oauth2", token) if token else None
    if key == "bitbucket":
        user = os.getenv("REPOGUARD_BITBUCKET_USERNAME")
        secret = os.getenv("REPOGUARD_BITBUCKET_APP_PASSWORD") or os.getenv("REPOGUARD_BITBUCKET_TOKEN")
        return _basic_header(user, secret) if user and secret else None
    if key == "azure_devops":
        token = os.getenv("REPOGUARD_AZURE_DEVOPS_PAT")
        return _basic_header("", token) if token else None
    if key in {"gitea", "gogs", "codeberg", "onedev"}:
        prefix = key.upper()
        token = os.getenv(f"REPOGUARD_{prefix}_TOKEN")
        user = os.getenv(f"REPOGUARD_{prefix}_USERNAME", "oauth2")
        return _basic_header(user, token) if token else None
    if key == "aws_codecommit":
        user = os.getenv("REPOGUARD_AWS_CODECOMMIT_USERNAME")
        password = os.getenv("REPOGUARD_AWS_CODECOMMIT_PASSWORD")
        return _basic_header(user, password) if user and password else None
    if key == "google_cloud_source_repositories":
        token = os.getenv("REPOGUARD_GCP_OAUTH_TOKEN")
        return f"Authorization: Bearer {token}" if token else None
    if key == "sourcehut":
        token = os.getenv("REPOGUARD_SOURCEHUT_TOKEN")
        return f"Authorization: Bearer {token}" if token else None
    return None


def credentials_configured(provider: str) -> bool:
    key = normalize_provider_key(provider)
    caps = _PROVIDER_CAPABILITIES.get(key)
    if not caps:
        return False
    return not caps.get("auth_required") or _auth_header(key) is not None


def _git_env(provider: str) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    header = _auth_header(provider)
    if header:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.extraHeader"
        env["GIT_CONFIG_VALUE_0"] = header
    return env


def _run_git(args: list[str], provider: str, timeout: int = 20, cwd: str | None = None, text: bool = True):
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=_git_env(provider),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            text=text,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git executable is not installed in the RepoGuard runtime") from exc
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Repository provider timed out") from exc


def repo_head_identity(provider: str, repo_input: str) -> tuple[str, str | None, str]:
    ref = build_clone_url(provider, repo_input)
    proc = _run_git(["ls-remote", ref.clone_url, "HEAD"], ref.provider, timeout=15)
    if proc.returncode != 0:
        return f"{ref.provider}:{ref.repository_id}", None, ref.repository_url
    line = (proc.stdout or "").strip().splitlines()
    head = line[0].split()[0] if line and line[0].split() else None
    return f"{ref.provider}:{ref.repository_id}", head, ref.repository_url


def _list_paths(repo_dir: str, provider: str, prefix: str) -> list[str]:
    proc = _run_git(["-C", repo_dir, "ls-tree", "-r", "--name-only", "HEAD", "--", prefix], provider, timeout=8)
    if proc.returncode != 0:
        return []
    return [p.strip() for p in (proc.stdout or "").splitlines() if p.strip()][:25]


def _git_show(repo_dir: str, provider: str, path: str, max_bytes: int = 1_000_000) -> str | None:
    proc = _run_git(["-C", repo_dir, "show", f"HEAD:{path}"], provider, timeout=8, text=False)
    if proc.returncode != 0:
        return None
    data = proc.stdout or b""
    if len(data) > max_bytes:
        return None
    return data.decode("utf-8", errors="replace")


def fetch_snapshot(provider: str, repo_input: str, core_files: list[str]) -> dict[str, Any]:
    ref = build_clone_url(provider, repo_input)
    capability = _PROVIDER_CAPABILITIES[ref.provider]
    if capability.get("auth_required") and not _auth_header(ref.provider):
        return {
            "ok": False,
            "error": "PROVIDER_AUTH_REQUIRED",
            "provider": ref.provider,
            "repository": ref.repository_id,
            "repository_url": ref.repository_url,
            "message": f"{ref.provider} adapter is active but this repository host requires configured credentials.",
        }

    with tempfile.TemporaryDirectory(prefix="repoguard-") as tmp:
        repo_dir = str(Path(tmp) / "repo")
        clone = _run_git(
            ["clone", "--depth", "1", "--filter=blob:none", "--no-checkout", ref.clone_url, repo_dir],
            ref.provider,
            timeout=30,
        )
        if clone.returncode != 0:
            return {
                "ok": False,
                "error": "REPO_NOT_PUBLIC_OR_INACCESSIBLE",
                "provider": ref.provider,
                "repository": ref.repository_id,
                "repository_url": ref.repository_url,
                "message": "Repository could not be fetched with the configured provider adapter.",
            }

        head_proc = _run_git(["-C", repo_dir, "rev-parse", "HEAD"], ref.provider, timeout=5)
        head_sha = (head_proc.stdout or "").strip() if head_proc.returncode == 0 else None
        branch_proc = _run_git(["-C", repo_dir, "branch", "--show-current"], ref.provider, timeout=5)
        default_branch = (branch_proc.stdout or "").strip() or "HEAD"
        ts_proc = _run_git(["-C", repo_dir, "show", "-s", "--format=%cI", "HEAD"], ref.provider, timeout=5)
        commit_timestamp = (ts_proc.stdout or "").strip() if ts_proc.returncode == 0 else None

        candidate_paths = list(dict.fromkeys(core_files + _PROVIDER_WORKFLOW_PATHS.get(ref.provider, [])))
        expanded: list[str] = []
        for path in candidate_paths:
            if path.endswith((".yml", ".yaml", ".json", ".md", ".txt", ".toml")) or path in {"Dockerfile", ".replit", "Pipfile", ".env", ".env.example", ".env.sample"}:
                expanded.append(path)
            else:
                expanded.extend(
                    p for p in _list_paths(repo_dir, ref.provider, path)
                    if p.endswith((".yml", ".yaml"))
                )

        files = []
        file_map: dict[str, str] = {}
        for path in dict.fromkeys(expanded):
            content = _git_show(repo_dir, ref.provider, path)
            if content is None:
                continue
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            file_map[path] = content
            files.append({
                "path": path,
                "size": len(content.encode("utf-8")),
                "content_hash": f"sha256:{digest}",
                "content": content,
            })

        return {
            "ok": True,
            "provider": ref.provider,
            "repository_id": ref.repository_id,
            "repository_url": ref.repository_url,
            "default_branch": default_branch,
            "commit_sha": head_sha,
            "commit_timestamp": commit_timestamp,
            "visibility": "authenticated" if _auth_header(ref.provider) else "public",
            "files": files,
            "file_map": file_map,
            "metadata": {"adapter_version": adapter_version(ref.provider)},
        }
