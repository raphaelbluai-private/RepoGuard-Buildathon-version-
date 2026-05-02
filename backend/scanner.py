"""
RepoGuard real-scan engine.

Pure deterministic checks against public GitHub repositories using only the
unauthenticated GitHub Contents API (no token required, no AI calls).

All checks are idempotent: same repo + same default branch HEAD → same findings,
score, and gates. Designed to be safe to call from a sync FastAPI handler
(FastAPI runs `def` endpoints in a threadpool).
"""

from __future__ import annotations

import re
import json
import base64
from datetime import datetime, timezone
from typing import Any

import requests

GITHUB_API = "https://api.github.com"
TIMEOUT = 8

SEVERITY_WEIGHTS = {"critical": 25, "high": 15, "medium": 8, "low": 3}

CORE_FILES = [
    "package.json", "pnpm-lock.yaml", "package-lock.json", "yarn.lock",
    "README.md", "readme.md", "Readme.md",
    ".env", ".env.example", ".env.sample",
    "Dockerfile", ".replit", "replit.nix",
    "vite.config.ts", "vite.config.js", "vite.config.mjs",
    "tsconfig.json",
    "requirements.txt", "pyproject.toml", "Pipfile",
]

# Token-shaped patterns. Conservative: each pattern is the documented prefix
# plus a length floor so we don't fire on sample placeholders like "sk-xxx".
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"),                            "OpenAI API key"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"),                            "GitHub personal access token"),
    (re.compile(r"gho_[A-Za-z0-9]{30,}"),                            "GitHub OAuth token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),                    "GitHub fine-grained PAT"),
    (re.compile(r"xoxb-[A-Za-z0-9-]{20,}"),                          "Slack bot token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"),                                "AWS access key ID"),
    (re.compile(r"AIza[A-Za-z0-9_-]{35}"),                           "Google API key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |)PRIVATE KEY-----"),
                                                                     "Private key block"),
]

# Patterns that indicate unsafe dynamic execution.
UNSAFE_PATTERNS = [
    (re.compile(r"\beval\s*\("),                                "eval()",                    "high"),
    (re.compile(r"\bexec\s*\("),                                "exec()",                    "high"),
    (re.compile(r"shell\s*=\s*True"),                           "shell=True",                "high"),
    (re.compile(r"child_process\.(?:exec|spawn)\s*\("),         "child_process.exec/spawn",  "medium"),
    (re.compile(r"\brm\s+-rf\s+/(?:\s|\"|'|$)"),                "rm -rf /",                  "critical"),
    (re.compile(r"curl\b[^\n]*\|\s*(?:bash|sh)\b"),             "curl | sh",                 "high"),
    (re.compile(r"wget\b[^\n]*\|\s*(?:bash|sh)\b"),             "wget | sh",                 "high"),
]

# Heuristic: code that reads env vars.
ENV_USAGE_RE = re.compile(
    r"process\.env\.[A-Z_][A-Z0-9_]*|os\.environ\[|os\.environ\.get\(|os\.getenv\(|getenv\("
)

# Accept "owner/repo", "github.com/owner/repo", "https://github.com/owner/repo[.git]".
_REPO_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:github\.com[/:])?"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9._-]{0,38}))"
    r"/"
    r"(?P<repo>[A-Za-z0-9](?:[A-Za-z0-9._-]{0,99}?))"
    r"(?:\.git)?/?$"
)

_GH_HEADERS = {
    "User-Agent": "RepoGuard-WarRoom/1.0",
    "Accept": "application/vnd.github+json",
}


# ─── Input parsing ────────────────────────────────────────────────────────────

def normalize_repo(s: str):
    """Return (owner, repo, error_or_None)."""
    s = (s or "").strip()
    if not s:
        return None, None, "Repository is required."
    # Strip trailing slashes / fragments / query strings
    s = s.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    m = _REPO_RE.search(s)
    if not m:
        return None, None, "Use owner/repo or a github.com URL."
    return m.group("owner"), m.group("repo"), None


# ─── GitHub fetching (unauthenticated, public repos only) ────────────────────

class GitHubRateLimited(Exception):
    """Raised when GitHub returns 403/429 mid-scan so the caller can fail fast."""
    pass


def _gh_get(url: str):
    return requests.get(url, headers=_GH_HEADERS, timeout=TIMEOUT)


def _is_rate_limited(r) -> bool:
    if r.status_code == 429:
        return True
    if r.status_code == 403:
        body_lower = (getattr(r, "text", "") or "").lower()
        if "rate limit" in body_lower or "api rate limit" in body_lower:
            return True
        if r.headers.get("X-RateLimit-Remaining") == "0":
            return True
    return False


def _fetch_file(owner: str, repo: str, path: str, ref: str):
    try:
        r = _gh_get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}?ref={ref}")
    except requests.RequestException:
        return None
    if _is_rate_limited(r):
        raise GitHubRateLimited()
    if r.status_code == 404:
        return None  # legitimate "file does not exist" — not a fetch failure
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("encoding") != "base64":
        return None
    raw = data.get("content") or ""
    if not raw:
        return None  # >1MB files come back without inline content
    try:
        return base64.b64decode(raw).decode("utf-8", errors="replace")
    except Exception:
        return None


def _list_workflows(owner: str, repo: str, ref: str):
    try:
        r = _gh_get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/.github/workflows?ref={ref}")
    except requests.RequestException:
        return []
    if _is_rate_limited(r):
        raise GitHubRateLimited()
    if r.status_code != 200:
        return []
    try:
        data = r.json()
    except ValueError:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "file":
            continue
        name = item.get("name", "")
        if name.endswith((".yml", ".yaml")):
            out.append(item["path"])
    return out[:10]  # cap to keep scan time bounded


# ─── Finding builder ─────────────────────────────────────────────────────────

class _FindingBuilder:
    def __init__(self):
        self.findings = []
        self._seen = set()
        self._counter = 0

    def add(self, *, category, severity, file, title, what, why, how, fix_plan):
        # De-dup identical findings.
        key = (category, file, title)
        if key in self._seen:
            return
        self._seen.add(key)
        self._counter += 1
        self.findings.append({
            "id": f"f{self._counter}",
            "category": category,
            "severity": severity,
            "file": file,
            "status": "open",
            "shortExplanation": title,
            "whatBroke": what,
            "whyMatters": why,
            "howToFix": how,
            "fixPlan": fix_plan,
        })


# ─── Check engine ────────────────────────────────────────────────────────────

def _normalize_readme_key(file_map):
    for k in ("README.md", "readme.md", "Readme.md"):
        if k in file_map:
            return k, file_map[k]
    return None, None


def _normalize_env_example_key(file_map):
    for k in (".env.example", ".env.sample"):
        if k in file_map:
            return k, file_map[k]
    return None, None


def _run_checks(file_map: dict[str, str]):
    fb = _FindingBuilder()

    has_env_usage = any(ENV_USAGE_RE.search(c) for c in file_map.values())
    has_env_committed = ".env" in file_map
    env_example_path, env_example_content = _normalize_env_example_key(file_map)
    has_env_example = env_example_path is not None
    has_package_json = "package.json" in file_map
    has_lockfile = any(p in file_map for p in ("pnpm-lock.yaml", "package-lock.json", "yarn.lock"))
    readme_path, readme_content = _normalize_readme_key(file_map)
    has_readme = readme_path is not None
    has_replit = ".replit" in file_map
    workflow_paths = [p for p in file_map if p.startswith(".github/workflows/")]

    pkg_scripts: dict = {}
    pkg_parse_failed = False
    if has_package_json:
        try:
            pkg = json.loads(file_map["package.json"])
            if isinstance(pkg, dict):
                scripts = pkg.get("scripts")
                if isinstance(scripts, dict):
                    pkg_scripts = scripts
        except Exception:
            pkg_parse_failed = True

    has_build = ("build" in pkg_scripts) if has_package_json else None
    has_start = (("start" in pkg_scripts) or ("dev" in pkg_scripts)) if has_package_json else None

    # ── Check 1: committed .env file ──
    if has_env_committed:
        fb.add(
            category="Secrets Exposure", severity="critical", file=".env",
            title=".env file committed to repository",
            what="A .env file is present and accessible at the repo's default branch.",
            why=("Anyone reading the repo (including bots that scrape public repos within minutes) can read every "
                 "environment value. Bots have been observed harvesting committed .env keys in under 5 minutes."),
            how="Remove .env from the repo, add it to .gitignore, rotate any secrets that were inside, and document expected variables in .env.example.",
            fix_plan=[
                "Add .env to .gitignore",
                "Run: git rm --cached .env",
                "Rotate every secret that was committed",
                "Re-create .env.example with placeholder values",
                "Commit and re-run the scan",
            ],
        )

    # ── Check 2: token-like values in any fetched file ──
    for path, content in file_map.items():
        for pat, label in SECRET_PATTERNS:
            if pat.search(content):
                fb.add(
                    category="Secrets Exposure", severity="critical", file=path,
                    title=f"{label} pattern detected in {path}",
                    what=f"A value matching the {label} pattern was found in {path}.",
                    why="Hardcoded credentials grant attackers immediate access to the upstream service. Anyone with read access to the repo gets the keys.",
                    how="Remove the literal value, store it in Replit Secrets, and replace with a runtime env lookup. Rotate the leaked credential at the provider.",
                    fix_plan=[
                        f"Locate and remove the value in {path}",
                        "Rotate the credential at the provider",
                        "Add the secret to Replit Secrets",
                        "Replace with a runtime env lookup",
                        "Re-run the scan to confirm",
                    ],
                )

    # ── Check 3: env usage but no .env.example ──
    if has_env_usage and not has_env_example and not has_env_committed:
        fb.add(
            category="Missing Environment Variable", severity="medium", file=".env.example",
            title="Code reads env vars but no .env.example exists",
            what="Code references process.env / os.environ / getenv but no .env.example documents which variables are required.",
            why="New contributors and the deploy environment will not know which variables to set, leading to silent crashes on startup.",
            how="Create .env.example listing every required variable with placeholder values.",
            fix_plan=[
                "List every env var the code reads",
                "Create .env.example with placeholder values",
                "Update README with a 'Required env vars' section",
                "Re-run the scan",
            ],
        )

    # ── Check 4: .env.example contains real-looking secrets ──
    if has_env_example and env_example_content:
        for pat, label in SECRET_PATTERNS:
            if pat.search(env_example_content):
                fb.add(
                    category="Secrets Exposure", severity="high", file=env_example_path,
                    title=f"{label} pattern in {env_example_path}",
                    what=f"{env_example_path} should hold placeholders only, but it contains a value matching the {label} pattern.",
                    why="If example values are treated as real secrets, real credentials get leaked to anyone who clones the repo.",
                    how="Replace the value with a clear placeholder like 'your-key-here' and rotate the credential if it was real.",
                    fix_plan=[
                        f"Replace the value with a placeholder in {env_example_path}",
                        "Rotate the credential at the provider if it was real",
                        "Re-run the scan",
                    ],
                )
                break

    # ── Check 5/6: package.json scripts ──
    if has_package_json and not pkg_parse_failed:
        if not has_build:
            fb.add(
                category="Dependency Risk", severity="medium", file="package.json",
                title="No 'build' script in package.json",
                what="package.json defines no 'build' script.",
                why="Most deploy targets need a build step. Without one, the deploy will either skip the build or fail.",
                how="Add a 'build' script to package.json that produces the production output.",
                fix_plan=[
                    "Open package.json",
                    "Add scripts.build with the right command for your stack",
                    "Test it locally",
                    "Re-run the scan",
                ],
            )
        if not has_start:
            fb.add(
                category="Dependency Risk", severity="medium", file="package.json",
                title="No 'start' or 'dev' script in package.json",
                what="package.json defines neither a 'start' nor 'dev' script.",
                why="Replit Deployments and most hosts run `npm start`. Without it, the app cannot be launched.",
                how="Add a 'start' script (or 'dev' for the development workflow).",
                fix_plan=[
                    "Open package.json",
                    "Add scripts.start that runs the server",
                    "Re-run the scan",
                ],
            )

    if has_package_json and not has_lockfile:
        fb.add(
            category="Dependency Risk", severity="low", file="package.json",
            title="No lockfile committed alongside package.json",
            what="package.json is present but no lockfile (pnpm-lock.yaml, package-lock.json, yarn.lock) is committed.",
            why="Without a lockfile, dependency versions can drift between developers and production, leading to non-reproducible builds.",
            how="Run your package manager's install command and commit the resulting lockfile.",
            fix_plan=[
                "Run your package manager (`pnpm install` / `npm install` / `yarn`)",
                "Commit the resulting lockfile",
                "Re-run the scan",
            ],
        )

    # ── Check 7-9: workflow files ──
    for wf in workflow_paths:
        wf_content = file_map[wf]
        if "permissions:" not in wf_content:
            fb.add(
                category="Permission Scope Risk", severity="high", file=wf,
                title="Workflow has no permissions block",
                what=f"{wf} has no `permissions:` block, so the GITHUB_TOKEN defaults to the repo-wide token scope.",
                why="An unscoped GITHUB_TOKEN gives any compromised step (malicious dep, supply-chain attack) full write access to the repo, including pushes to main.",
                how="Add an explicit `permissions:` block at workflow root, granting only the minimum scope each step needs.",
                fix_plan=[
                    "Add permissions: block at workflow root",
                    "Set contents: read for read-only jobs",
                    "Grant write scopes only where needed",
                    "Re-run the scan",
                ],
            )
        if re.search(r"permissions:\s*write-all", wf_content):
            fb.add(
                category="Permission Scope Risk", severity="critical", file=wf,
                title="Workflow uses permissions: write-all",
                what=f"{wf} explicitly grants write-all on all token scopes.",
                why="Equivalent to handing a compromised dependency a master key. Any RCE in CI becomes a full repo takeover.",
                how="Replace `write-all` with the minimum specific scopes each job actually needs.",
                fix_plan=[
                    "Remove the `write-all` line",
                    "Add specific scopes per job (contents, pull-requests, etc.)",
                    "Re-run the scan",
                ],
            )

    # ── Check 10: .replit deployment block ──
    if has_replit and "[deployment]" not in file_map[".replit"]:
        fb.add(
            category="Deployment Blocker", severity="high", file=".replit",
            title=".replit has no [deployment] block",
            what="The .replit file does not declare a [deployment] section, so Replit Deployments has no build or run command to execute.",
            why="Pressing Publish results in an immediate build error. The app cannot ship until this is corrected.",
            how="Add a [deployment] block with explicit build and run commands.",
            fix_plan=[
                "Open .replit",
                "Add [deployment] section",
                "Set build = your build command",
                "Set run = your start command",
                "Press Publish and confirm it succeeds",
            ],
        )

    # ── Check 11: unsafe execution patterns ──
    for path, content in file_map.items():
        for pat, label, sev in UNSAFE_PATTERNS:
            if pat.search(content):
                fb.add(
                    category="Unsafe Shell Execution", severity=sev, file=path,
                    title=f"Use of {label} detected in {path}",
                    what=f"{path} contains a use of `{label}`, a known-dangerous pattern.",
                    why="If the input is ever attacker-controlled, this becomes arbitrary code or shell execution. Even when 'safe today', it is brittle to future regressions.",
                    how=f"Replace `{label}` with a safer alternative — strict input validation, an allowlist, or a non-shell API.",
                    fix_plan=[
                        f"Find the use of {label} in {path}",
                        "Replace with a safer alternative",
                        "Add a regression test that rejects malicious input",
                        "Re-run the scan",
                    ],
                )

    # ── Check 12: README presence + content ──
    if not has_readme:
        fb.add(
            category="Documentation Readiness", severity="low", file="README.md",
            title="No README.md found",
            what="The repository has no README.md file.",
            why="Visitors, contributors, and even your future self will not know what the project does, how to install it, or how to run it.",
            how="Create a README.md with at least: project description, install steps, run command, deploy notes.",
            fix_plan=[
                "Create README.md",
                "Add: 'About' / 'Install' / 'Run' / 'Deploy' sections",
                "Re-run the scan",
            ],
        )
    elif readme_content:
        readme_lower = readme_content.lower()
        missing = []
        if not re.search(r"\b(install|setup|getting started)\b", readme_lower):
            missing.append("install/setup")
        if not re.search(r"\b(run|usage|start)\b", readme_lower):
            missing.append("run/usage")
        if missing:
            fb.add(
                category="Documentation Readiness", severity="low", file=readme_path,
                title="README is missing key sections",
                what=f"{readme_path} exists but does not mention: {', '.join(missing)}.",
                why="Without these sections, new users cannot get the project running.",
                how="Add the missing sections to the README.",
                fix_plan=[
                    f"Add a section for: {', '.join(missing)}",
                    "Include the exact commands to install and run",
                    "Re-run the scan",
                ],
            )

    signals = {
        "has_env_committed": has_env_committed,
        "has_env_example": has_env_example,
        "has_env_usage": has_env_usage,
        "has_package_json": has_package_json,
        "has_build": has_build,
        "has_start": has_start,
        "has_workflows": bool(workflow_paths),
        "has_readme": has_readme,
        "has_replit": has_replit,
        "has_replit_deployment": has_replit and "[deployment]" in file_map.get(".replit", ""),
    }
    return fb.findings, signals


# ─── Score, status, gates ────────────────────────────────────────────────────

def _calc_score(findings):
    score = 100
    for f in findings:
        score -= SEVERITY_WEIGHTS.get(f["severity"], 0)
    return max(0, score)


def _derive_status(score, findings):
    has_critical = any(f["severity"] == "critical" for f in findings)
    has_high = any(f["severity"] == "high" for f in findings)
    if has_critical or score < 60:
        return "SHIP_BLOCKED"
    if has_high or score < 85:
        return "NEEDS_REVIEW"
    return "SAFE_TO_SHIP"


def _derive_gates(signals, findings):
    has_secrets = any(f["category"] == "Secrets Exposure" for f in findings)
    has_env_finding = any(f["category"] == "Missing Environment Variable" for f in findings)
    has_workflow_perm = any(f["category"] == "Permission Scope Risk" for f in findings)
    has_unsafe = any(f["category"] == "Unsafe Shell Execution" for f in findings)
    has_critical_unsafe = any(
        f["category"] == "Unsafe Shell Execution" and f["severity"] == "critical"
        for f in findings
    )
    has_doc_finding = any(f["category"] == "Documentation Readiness" for f in findings)
    has_replit_dep_finding = any(f["category"] == "Deployment Blocker" for f in findings)

    secrets_count = sum(1 for f in findings if f["category"] == "Secrets Exposure")

    gates = []
    gates.append({
        "id": "g1", "label": "No exposed secrets",
        "state": "fail" if has_secrets else "pass",
        "detail": f"{secrets_count} finding(s)" if has_secrets else "Scanner found no leaked credentials",
    })

    if signals["has_env_usage"]:
        gates.append({
            "id": "g2", "label": "Environment variables documented",
            "state": "fail" if has_env_finding else "pass",
            "detail": "Missing .env.example" if has_env_finding else ".env.example present",
        })
    else:
        gates.append({
            "id": "g2", "label": "Environment variables documented",
            "state": "pass", "detail": "No env var usage detected",
        })

    if signals["has_package_json"]:
        gates.append({
            "id": "g3", "label": "Build command detected",
            "state": "pass" if signals["has_build"] else "fail",
            "detail": "scripts.build present" if signals["has_build"] else "No 'build' script",
        })
        gates.append({
            "id": "g4", "label": "Start command detected",
            "state": "pass" if signals["has_start"] else "fail",
            "detail": "scripts.start/dev present" if signals["has_start"] else "No 'start' or 'dev' script",
        })
    else:
        gates.append({"id": "g3", "label": "Build command detected", "state": "warning",
                      "detail": "No package.json found — not a Node project"})
        gates.append({"id": "g4", "label": "Start command detected", "state": "warning",
                      "detail": "No package.json found — not a Node project"})

    if signals["has_workflows"]:
        gates.append({
            "id": "g5", "label": "Workflow files validated",
            "state": "fail" if has_workflow_perm else "pass",
            "detail": "Permission scope risk detected" if has_workflow_perm else "Workflow permissions look scoped",
        })
    else:
        gates.append({"id": "g5", "label": "Workflow files validated", "state": "pass",
                      "detail": "No workflow files found"})

    gates.append({
        "id": "g6", "label": "No critical unsafe execution patterns",
        "state": "fail" if has_critical_unsafe else ("warning" if has_unsafe else "pass"),
        "detail": "Critical unsafe pattern detected" if has_critical_unsafe
                  else ("Non-critical unsafe pattern detected" if has_unsafe else "Clean"),
    })

    gates.append({
        "id": "g7", "label": "README/setup instructions present",
        "state": "fail" if has_doc_finding else "pass",
        "detail": "Documentation finding open" if has_doc_finding else "README documents setup",
    })

    if signals["has_replit_deployment"]:
        gates.append({"id": "g8", "label": "Replit deployment path identifiable",
                      "state": "pass", "detail": "[deployment] block present"})
    elif has_replit_dep_finding:
        gates.append({"id": "g8", "label": "Replit deployment path identifiable",
                      "state": "fail", "detail": "[deployment] block missing"})
    else:
        gates.append({"id": "g8", "label": "Replit deployment path identifiable",
                      "state": "warning", "detail": "No .replit file found"})

    return gates


# ─── Public API ──────────────────────────────────────────────────────────────

def scan_repo(repo_input: str) -> dict[str, Any]:
    owner, repo, err = normalize_repo(repo_input)
    if err:
        return {"ok": False, "error": "INVALID_INPUT", "message": err}

    try:
        meta_r = _gh_get(f"{GITHUB_API}/repos/{owner}/{repo}")
    except requests.RequestException:
        return {"ok": False, "error": "NETWORK_ERROR",
                "message": "Could not reach GitHub. Try again or use the sample scan."}

    if meta_r.status_code == 404:
        return {"ok": False, "error": "REPO_NOT_FOUND",
                "message": f"Public repo {owner}/{repo} not found."}
    if meta_r.status_code == 403:
        body_lower = (meta_r.text or "").lower()
        if "rate limit" in body_lower:
            return {"ok": False, "error": "RATE_LIMIT",
                    "message": "GitHub API rate limit reached. Wait a minute or use the sample scan."}
        return {"ok": False, "error": "GITHUB_FORBIDDEN",
                "message": "GitHub denied the request (403)."}
    if meta_r.status_code == 451:
        return {"ok": False, "error": "BLOCKED",
                "message": "Repository is blocked or unavailable."}
    if meta_r.status_code != 200:
        return {"ok": False, "error": "GITHUB_ERROR",
                "message": f"GitHub returned HTTP {meta_r.status_code}"}

    try:
        meta = meta_r.json()
    except ValueError:
        return {"ok": False, "error": "GITHUB_ERROR", "message": "GitHub response was not JSON."}

    if meta.get("private"):
        return {"ok": False, "error": "NOT_PUBLIC",
                "message": "Repository is private. RepoGuard only scans public repos."}

    default_branch = meta.get("default_branch") or "main"

    file_map: dict[str, str] = {}
    files_seen: list[str] = []
    try:
        for path in CORE_FILES:
            c = _fetch_file(owner, repo, path, default_branch)
            if c is not None:
                file_map[path] = c
                files_seen.append(path)

        for wf_path in _list_workflows(owner, repo, default_branch):
            c = _fetch_file(owner, repo, wf_path, default_branch)
            if c is not None:
                file_map[wf_path] = c
                files_seen.append(wf_path)
    except GitHubRateLimited:
        return {
            "ok": False,
            "error": "RATE_LIMIT",
            "message": (
                "GitHub API rate limit reached partway through the scan. "
                "Wait a minute and try again, or use the sample scan."
            ),
        }

    findings, signals = _run_checks(file_map)
    score = _calc_score(findings)
    status = _derive_status(score, findings)
    gates = _derive_gates(signals, findings)

    return {
        "ok": True,
        "repo": {
            "owner": owner,
            "name": repo,
            "fullName": f"{owner}/{repo}",
            "url": meta.get("html_url"),
            "defaultBranch": default_branch,
            "stars": meta.get("stargazers_count", 0),
            "language": meta.get("language"),
            "description": meta.get("description"),
        },
        "scanTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "filesScanned": files_seen,
        "findings": findings,
        "score": score,
        "scoreProjected": 100,
        "status": status,
        "gates": gates,
    }
