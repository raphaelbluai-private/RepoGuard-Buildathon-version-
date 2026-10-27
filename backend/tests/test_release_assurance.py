import release_assurance as ra


def test_release_assurance_fails_closed_without_external_governance_evidence(monkeypatch):
    for key in (
        "REPOGUARD_BRANCH_PROTECTION_VERIFIED",
        "REPOGUARD_REQUIRED_CHECKS_VERIFIED",
        "REPOGUARD_RELEASE_SIGNATURE_VERIFIED",
        "REPOGUARD_PUBLIC_SOURCE_APPROVED",
    ):
        monkeypatch.delenv(key, raising=False)
    result = ra.release_assurance(
        branch="x402-production", source_sha="a" * 40, repository_visibility="public"
    )
    assert result["status"] == "BLOCKED"
    assert result["release_authorized"] is False
    assert "branch_protection_unverified" in result["blockers"]
    assert "public_source_disposition_unapproved" in result["blockers"]


def test_release_assurance_accepts_observed_controls_but_never_self_authorizes(monkeypatch):
    monkeypatch.setenv("REPOGUARD_BRANCH_PROTECTION_VERIFIED", "1")
    monkeypatch.setenv("REPOGUARD_REQUIRED_CHECKS_VERIFIED", "1")
    monkeypatch.setenv("REPOGUARD_RELEASE_SIGNATURE_VERIFIED", "1")
    monkeypatch.setenv("REPOGUARD_PUBLIC_SOURCE_APPROVED", "1")
    result = ra.release_assurance(
        branch="x402-production", source_sha="b" * 40, repository_visibility="public"
    )
    assert result["status"] == "ASSURED"
    assert result["release_authorized"] is False
    assert result["blockers"] == []


def test_release_assurance_rejects_noncanonical_branch_and_short_sha(monkeypatch):
    result = ra.release_assurance(branch="demo", source_sha="abc123", repository_visibility="private")
    assert "release_branch_not_canonical" in result["blockers"]
    assert "source_sha_not_exact" in result["blockers"]
