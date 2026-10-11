from source_adapters import _git_env, fetch_snapshot


def test_public_git_environment_never_contains_provider_credentials(monkeypatch):
    monkeypatch.setenv("REPOGUARD_GITHUB_TOKEN", "must-not-leave-process")

    env = _git_env("github")

    assert "must-not-leave-process" not in repr(env)
    assert env["GIT_CONFIG_COUNT"] == "2"
    assert env["GIT_CONFIG_KEY_0"] == "http.followRedirects"
    assert env["GIT_CONFIG_VALUE_0"] == "false"
    assert env["GIT_CONFIG_KEY_1"] == "credential.helper"
    assert env["GIT_CONFIG_VALUE_1"] == ""
    assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"


def test_authenticated_only_provider_is_rejected_in_public_scan_mode(monkeypatch):
    monkeypatch.setenv("REPOGUARD_AWS_CODECOMMIT_USERNAME", "user")
    monkeypatch.setenv("REPOGUARD_AWS_CODECOMMIT_PASSWORD", "secret")
    monkeypatch.setattr(
        "source_adapters.validate_repository_destination",
        lambda provider, url: type("Destination", (), {"url": url})(),
    )

    result = fetch_snapshot("aws_codecommit", "us-east-1/demo", [])

    assert result["ok"] is False
    assert result["error"] == "PROVIDER_AUTH_REQUIRED"
    assert "public-only" in result["message"]
