import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_container_runs_as_non_root_with_bounded_writable_paths():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "USER repoguard" in dockerfile
    assert "REPOGUARD_CACHE_DB=/data/repoguard-cache.sqlite3" in dockerfile
    assert "REPOGUARD_TELEMETRY_DB=/data/repoguard-commerce.sqlite3" in dockerfile
    assert "TMPDIR=/tmp/repoguard" in dockerfile
    assert "chown -R repoguard:repoguard /data /tmp/repoguard" in dockerfile
    assert "uv sync --frozen --no-dev --no-install-project" in dockerfile


def test_package_manager_and_native_build_policy_are_explicit():
    package = json.loads((ROOT / "package.json").read_text())
    assert package["packageManager"].startswith("pnpm@9.")
    workspace = yaml.safe_load((ROOT / "pnpm-workspace.yaml").read_text())
    assert workspace["onlyBuiltDependencies"] == ["esbuild"]


def test_ci_permissions_are_least_privilege():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert workflow["permissions"] == {"contents": "read"}
    for job in workflow["jobs"].values():
        assert job.get("permissions", {"contents": "read"}) == {"contents": "read"}
