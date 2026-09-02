import pytest

from source_adapters import build_clone_url, normalize_provider_key, provider_capabilities


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


def test_full_https_url_is_accepted_for_self_hosted_adapter():
    ref = build_clone_url("gitea", "https://git.example.com/acme/widget.git")
    assert ref.clone_url == "https://git.example.com/acme/widget.git"
    assert ref.repository_id == "acme/widget"
