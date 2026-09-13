import json

import scanner


def _rules(file_map):
    findings, signals = scanner._run_checks(file_map)
    return findings, signals


def _rule_ids(findings):
    return {f["ruleId"] for f in findings}


def _clean_fixture():
    return {
        "package.json": json.dumps({"scripts": {"build": "vite build", "start": "node server.js"}}),
        "pnpm-lock.yaml": "lockfileVersion: '9.0'",
        "README.md": "# App\n## Install\npnpm install\n## Run\npnpm start\n",
        ".env.example": "DATABASE_URL=your-value-here\n",
        ".github/workflows/ci.yml": "permissions:\n  contents: read\n",
    }


def test_clean_fixture_safe_to_ship():
    findings, _ = _rules(_clean_fixture())
    score = scanner._calc_score(findings)
    assert scanner._derive_status(score, findings) == "SAFE_TO_SHIP"


def test_clean_fixture_is_repeatable():
    first, _ = _rules(_clean_fixture())
    second, _ = _rules(_clean_fixture())
    assert first == second
    assert scanner._calc_score(first) == scanner._calc_score(second)


def test_committed_env_is_ship_blocked():
    files = _clean_fixture() | {".env": "DATABASE_URL=postgres://prod"}
    findings, _ = _rules(files)
    assert "ENV_COMMITTED" in _rule_ids(findings)
    assert scanner._derive_status(scanner._calc_score(findings), findings) == "SHIP_BLOCKED"


def test_write_all_is_ship_blocked():
    files = _clean_fixture() | {".github/workflows/ci.yml": "permissions: write-all\n"}
    findings, _ = _rules(files)
    assert "WORKFLOW_WRITE_ALL" in _rule_ids(findings)
    assert scanner._derive_status(scanner._calc_score(findings), findings) == "SHIP_BLOCKED"


def test_workflow_without_permissions_needs_review():
    files = _clean_fixture() | {".github/workflows/ci.yml": "name: ci\non: push\n"}
    findings, _ = _rules(files)
    assert "WORKFLOW_NO_PERMISSIONS" in _rule_ids(findings)
    assert scanner._derive_status(scanner._calc_score(findings), findings) == "NEEDS_REVIEW"


def test_missing_build_script_detected():
    files = _clean_fixture() | {
        "package.json": json.dumps({"scripts": {"start": "node server.js"}})
    }
    findings, _ = _rules(files)
    assert "MISSING_BUILD_SCRIPT" in _rule_ids(findings)


def test_missing_start_script_detected():
    files = _clean_fixture() | {
        "package.json": json.dumps({"scripts": {"build": "vite build"}})
    }
    findings, _ = _rules(files)
    assert "MISSING_START_SCRIPT" in _rule_ids(findings)


def test_missing_lockfile_detected():
    files = _clean_fixture()
    files.pop("pnpm-lock.yaml")
    findings, _ = _rules(files)
    assert "NO_LOCKFILE" in _rule_ids(findings)


def test_env_usage_without_example_detected():
    files = _clean_fixture()
    files.pop(".env.example")
    files["app.py"] = 'token = os.getenv("API_TOKEN")'
    findings, _ = _rules(files)
    assert "ENV_UNDOCUMENTED" in _rule_ids(findings)


def test_real_secret_in_env_example_detected():
    files = _clean_fixture() | {
        ".env.example": "OPENAI_API_KEY=sk-123456789012345678901234567890"
    }
    findings, _ = _rules(files)
    assert "SECRET_IN_EXAMPLE" in _rule_ids(findings)


def test_github_pat_pattern_detected():
    files = _clean_fixture() | {"config.txt": "ghp_123456789012345678901234567890123456"}
    findings, _ = _rules(files)
    assert "SECRET_PATTERN" in _rule_ids(findings)


def test_aws_access_key_pattern_detected():
    files = _clean_fixture() | {"config.txt": "AKIA1234567890ABCDEF"}
    findings, _ = _rules(files)
    assert "SECRET_PATTERN" in _rule_ids(findings)


def test_private_key_pattern_detected():
    files = _clean_fixture() | {"key.pem": "-----BEGIN PRIVATE KEY-----\nabc"}
    findings, _ = _rules(files)
    assert "SECRET_PATTERN" in _rule_ids(findings)


def test_curl_pipe_sh_detected():
    files = _clean_fixture() | {"install.sh": "curl https://example.com/x | sh"}
    findings, _ = _rules(files)
    assert "UNSAFE_EXEC" in _rule_ids(findings)


def test_wget_pipe_bash_detected():
    files = _clean_fixture() | {"install.sh": "wget https://example.com/x | bash"}
    findings, _ = _rules(files)
    assert "UNSAFE_EXEC" in _rule_ids(findings)


def test_shell_true_detected():
    files = _clean_fixture() | {"runner.py": "subprocess.run(cmd, shell=True)"}
    findings, _ = _rules(files)
    assert "UNSAFE_EXEC" in _rule_ids(findings)


def test_eval_detected():
    files = _clean_fixture() | {"runner.py": "result = eval(user_input)"}
    findings, _ = _rules(files)
    assert "UNSAFE_EXEC" in _rule_ids(findings)


def test_replit_without_deployment_detected():
    files = _clean_fixture() | {".replit": "run = 'python main.py'"}
    findings, _ = _rules(files)
    assert "REPLIT_NO_DEPLOYMENT" in _rule_ids(findings)


def test_replit_with_deployment_not_flagged():
    files = _clean_fixture() | {".replit": "[deployment]\nrun = ['python','main.py']"}
    findings, _ = _rules(files)
    assert "REPLIT_NO_DEPLOYMENT" not in _rule_ids(findings)


def test_missing_readme_detected():
    files = _clean_fixture()
    files.pop("README.md")
    findings, _ = _rules(files)
    assert "README_MISSING" in _rule_ids(findings)


def test_inadequate_readme_detected():
    files = _clean_fixture() | {"README.md": "# App\nA small project.\n"}
    findings, _ = _rules(files)
    assert "README_INCOMPLETE" in _rule_ids(findings)


def test_normalize_owner_repo():
    assert scanner.normalize_repo("openai/openai-python")[:2] == ("openai", "openai-python")


def test_normalize_full_url():
    assert scanner.normalize_repo("https://github.com/openai/openai-python.git")[:2] == ("openai", "openai-python")


def test_normalize_tree_url():
    assert scanner.normalize_repo("https://github.com/openai/openai-python/tree/main")[:2] == ("openai", "openai-python")


def test_normalize_invalid_input():
    owner, repo, err = scanner.normalize_repo("")
    assert owner is None and repo is None and err


def test_score_deducts_by_severity():
    findings = [
        {"severity": "critical"},
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "low"},
    ]
    assert scanner._calc_score(findings) == 49


def test_score_never_below_zero():
    findings = [{"severity": "critical"}] * 10
    assert scanner._calc_score(findings) == 0


def test_high_finding_forces_needs_review():
    findings = [{"severity": "high"}]
    assert scanner._derive_status(85, findings) == "NEEDS_REVIEW"


def test_critical_finding_forces_ship_blocked():
    findings = [{"severity": "critical"}]
    assert scanner._derive_status(90, findings) == "SHIP_BLOCKED"


def test_score_under_60_forces_ship_blocked():
    assert scanner._derive_status(59, []) == "SHIP_BLOCKED"


def test_safe_status_at_clean_threshold():
    assert scanner._derive_status(85, []) == "SAFE_TO_SHIP"
