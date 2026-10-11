from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


class UnsafeRepositoryDestination(ValueError):
    """Caller-selected repository destination violates the outbound policy."""


@dataclass(frozen=True)
class ValidatedDestination:
    url: str
    hostname: str
    port: int
    resolved_addresses: tuple[str, ...]


_PROVIDER_HOSTS: dict[str, tuple[str, ...]] = {
    "github": ("github.com",),
    "gitlab": ("gitlab.com",),
    "bitbucket": ("bitbucket.org",),
    "azure_devops": ("dev.azure.com",),
    "codeberg": ("codeberg.org",),
    "aws_codecommit": ("git-codecommit.*.amazonaws.com",),
    "google_cloud_source_repositories": ("source.developers.google.com",),
    "sourcehut": ("git.sr.ht",),
    "sourceforge": ("git.code.sf.net",),
}
_SELF_HOSTED = {"gitea", "gogs", "onedev"}


def _configured_self_hosted_hosts() -> tuple[str, ...]:
    return tuple(
        value.strip().lower().rstrip(".")
        for value in os.getenv("REPOGUARD_SELF_HOSTED_GIT_HOSTS", "").split(",")
        if value.strip()
    )


def _host_matches(hostname: str, pattern: str) -> bool:
    if pattern.startswith("*."):
        return hostname.endswith(pattern[1:]) and hostname != pattern[2:]
    if "*" in pattern:
        prefix, suffix = pattern.split("*", 1)
        middle = hostname.removeprefix(prefix).removesuffix(suffix)
        return hostname.startswith(prefix) and hostname.endswith(suffix) and bool(middle)
    return hostname == pattern


def _allowed_hosts(provider: str) -> tuple[str, ...]:
    if provider in _SELF_HOSTED:
        hosts = _configured_self_hosted_hosts()
        if not hosts:
            raise UnsafeRepositoryDestination(
                "Self-hosted repository providers require an explicit host allowlist."
            )
        return hosts
    try:
        return _PROVIDER_HOSTS[provider]
    except KeyError as exc:
        raise UnsafeRepositoryDestination("Repository provider has no outbound host policy.") from exc


def validate_repository_destination(
    provider: str,
    url: str,
    *,
    resolver=socket.getaddrinfo,
) -> ValidatedDestination:
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise UnsafeRepositoryDestination("Repository destination must use HTTPS.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeRepositoryDestination("Repository URLs cannot contain credentials.")
    if parsed.fragment:
        raise UnsafeRepositoryDestination("Repository URLs cannot contain fragments.")
    if parsed.query:
        raise UnsafeRepositoryDestination("Repository URLs cannot contain query parameters.")
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise UnsafeRepositoryDestination("Repository URL must contain a hostname.")
    try:
        port = parsed.port or 443
    except ValueError as exc:
        raise UnsafeRepositoryDestination("Repository URL contains an invalid port.") from exc
    if port != 443:
        raise UnsafeRepositoryDestination("Repository destination must use HTTPS port 443.")
    if not any(_host_matches(hostname, allowed) for allowed in _allowed_hosts(provider)):
        raise UnsafeRepositoryDestination(
            "Repository hostname does not match the selected provider allowlist."
        )

    try:
        answers = resolver(hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeRepositoryDestination("Repository hostname could not be safely resolved.") from exc
    addresses = tuple(sorted({str(answer[4][0]) for answer in answers}))
    if not addresses:
        raise UnsafeRepositoryDestination("Repository hostname returned no usable addresses.")
    for value in addresses:
        try:
            address = ipaddress.ip_address(value.split("%", 1)[0])
        except ValueError as exc:
            raise UnsafeRepositoryDestination("Repository hostname returned an invalid address.") from exc
        if (
            not address.is_global
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise UnsafeRepositoryDestination(
                "Repository destination must resolve only to the public network."
            )

    canonical_netloc = hostname
    return ValidatedDestination(
        url=urlunsplit(("https", canonical_netloc, parsed.path, parsed.query, "")),
        hostname=hostname,
        port=port,
        resolved_addresses=addresses,
    )
