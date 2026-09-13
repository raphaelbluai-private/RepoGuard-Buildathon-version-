import pytest

from source_adapters import (
    _git_env,
    build_clone_url,
    normalize_provider_key,
    provider_capabilities,
)


def test_all_original_source_adapters_are_active():
    caps = provider_capabilities()
    expected = {
        "github", "gitlab", "bitbucket", "azure_devops", "gitea", "gogs",
        "codeberg", "aws_codecommit", "google_cloud_source_repositories",
        "sourcehut", "onedev", "sourceforge",
    }
    assert expected <= set(caps)
    assert all(caps[p]["status"] == "active" for p in expected)


def test_provider_aliases_normalize():
    assert normalize_provider_key("Azure DevOps") == "azure_devops"
    assert normalize_provider_key("google-cloud-source-repositories") == "google_cloud_source_repositories"
    assert normalize_provider_key("SourceHut") == "sourcehut"


@pytest.mark.parametrize("provider,repo,expected", [
    ("github", "owner/repo", "https://github.com/owner/repo.git"),
    ("gitlab", "group/repo", "https://gitlab.com/group/repo.git"),
    ("bitbucket", "workspace/repo", "https://bitbucket.org/workspace/repo.git"),
    ("codeberg", "owner/repo", "https://codeberg.org/owner/repo.git"),
    ("azure_devops", "org/project/repo", "https://dev.azure.com/org/project/_git/repo"),
    ("sourcehut", "user/repo", "https://git.sr.ht/~user/repo"),
    ("sourceforge", "project/repo", "https://git.code.sf.net/p/project/repo"),
    ("aws_codecommit", "us-east-2/MyDemoRepo", "https://git-codecommit.us-east-2.amazonaws.com/v1/repos/MyDemoRepo"),
    ("google_cloud_source_repositories", "my-project/my-repo", "https://source.developers.google.com/p/my-project/r/my-repo"),
])
def test_build_clone_url_for_hosted_providers(provider, repo, expected):
    assert build_clone_url(provider, repo).clone_url == expected


def test_self_hosted_adapters_require_full_url():
    for provider in ("gitea", "gogs", "onedev"):
        with pytest.raises(ValueError):
            build_clone_url(provider, "owner/repo")


def test_full_https_url_is_accepted_for_self_hosted_adapter_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("REPOGUARD_ALLOW_SELF_HOSTED_PROVIDERS", "1")
    monkeypatch.setattr("source_adapters._resolve_host_ips", lambda host: {"203.0.113.10"})
    ref = build_clone_url("gitea", "https://git.example.com/acme/widget.git")
    assert ref.clone_url == "https://git.example.com/acme/widget.git"
    assert ref.repository_id == "acme/widget"


def test_self_hosted_full_url_is_blocked_by_default(monkeypatch):
    monkeypatch.delenv("REPOGUARD_ALLOW_SELF_HOSTED_PROVIDERS", raising=False)
    with pytest.raises(ValueError, match="self-hosted provider URLs are disabled"):
        build_clone_url("gitea", "https://git.example.com/acme/widget.git")


def test_http_clone_urls_are_rejected():
    with pytest.raises(ValueError, match="HTTPS"):
        build_clone_url("github", "http://github.com/acme/widget.git")


def test_hosted_provider_rejects_mismatched_host():
    with pytest.raises(ValueError, match="does not match provider"):
        build_clone_url("gitlab", "https://attacker.example/acme/widget.git")


def test_clone_url_rejects_embedded_credentials():
    with pytest.raises(ValueError, match="embedded credentials"):
        build_clone_url("github", "https://user:pass@github.com/acme/widget.git")


def test_self_hosted_private_ip_is_rejected_even_when_enabled(monkeypatch):
    monkeypatch.setenv("REPOGUARD_ALLOW_SELF_HOSTED_PROVIDERS", "1")
    with pytest.raises(ValueError, match="private or reserved"):
        build_clone_url("gitea", "https://127.0.0.1/acme/widget.git")


def test_git_auth_header_is_scoped_to_repository_host(monkeypatch):
    monkeypatch.setenv("REPOGUARD_GITLAB_TOKEN", "test-token")
    env = _git_env("gitlab", "https://gitlab.com/acme/widget.git")
    assert env["GIT_CONFIG_KEY_0"] == "http.https://gitlab.com/.extraHeader"
    assert env["GIT_CONFIG_KEY_1"] == "http.followRedirects"
    assert env["GIT_CONFIG_VALUE_1"] == "false"
