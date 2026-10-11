import socket

import pytest

from network_policy import UnsafeRepositoryDestination, validate_repository_destination


def public_resolver(host, port, *, type=socket.SOCK_STREAM):
    return [(socket.AF_INET, type, 6, "", ("93.184.216.34", port))]


@pytest.mark.parametrize(
    "provider,url",
    [
        ("github", "http://github.com/acme/repo.git"),
        ("github", "https://token@github.com/acme/repo.git"),
        ("github", "https://github.com/acme/repo.git#fragment"),
        ("github", "https://github.com/acme/repo.git?token=secret"),
        ("github", "https://github.com:8443/acme/repo.git"),
        ("gitlab", "https://attacker.example/acme/repo.git"),
        ("github", "https://gitlab.com/acme/repo.git"),
    ],
)
def test_repository_destination_rejects_unsafe_url_shapes(provider, url):
    with pytest.raises(UnsafeRepositoryDestination):
        validate_repository_destination(provider, url, resolver=public_resolver)


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254", "224.0.0.1", "192.0.2.1"],
)
def test_repository_destination_rejects_non_public_resolution(address):
    def resolver(host, port, *, type=socket.SOCK_STREAM):
        return [(socket.AF_INET, type, 6, "", (address, port))]

    with pytest.raises(UnsafeRepositoryDestination, match="public network"):
        validate_repository_destination("github", "https://github.com/acme/repo.git", resolver=resolver)


def test_repository_destination_accepts_canonical_provider_host():
    destination = validate_repository_destination(
        "github", "https://github.com/acme/repo.git", resolver=public_resolver
    )
    assert destination.hostname == "github.com"
    assert destination.port == 443
    assert destination.url == "https://github.com/acme/repo.git"


def test_self_hosted_provider_requires_explicit_host_allowlist(monkeypatch):
    with pytest.raises(UnsafeRepositoryDestination, match="allowlist"):
        validate_repository_destination(
            "gitea", "https://git.example.com/acme/repo.git", resolver=public_resolver
        )
    monkeypatch.setenv("REPOGUARD_SELF_HOSTED_GIT_HOSTS", "git.example.com")
    destination = validate_repository_destination(
        "gitea", "https://git.example.com/acme/repo.git", resolver=public_resolver
    )
    assert destination.hostname == "git.example.com"
