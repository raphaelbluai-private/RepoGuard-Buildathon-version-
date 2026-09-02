from provider_credentials import (
    provider_connection_status,
    provider_credential_requirements,
)


def test_google_and_aws_publish_required_secret_names_without_values(monkeypatch):
    for name in [
        "REPOGUARD_GCP_OAUTH_TOKEN",
        "REPOGUARD_AWS_CODECOMMIT_USERNAME",
        "REPOGUARD_AWS_CODECOMMIT_PASSWORD",
    ]:
        monkeypatch.delenv(name, raising=False)

    gcp = provider_credential_requirements("google_cloud_source_repositories")
    aws = provider_credential_requirements("aws_codecommit")

    assert gcp["required"] is True
    assert gcp["environment_variables"] == ["REPOGUARD_GCP_OAUTH_TOKEN"]
    assert aws["required"] is True
    assert aws["environment_variables"] == [
        "REPOGUARD_AWS_CODECOMMIT_USERNAME",
        "REPOGUARD_AWS_CODECOMMIT_PASSWORD",
    ]
    assert "value" not in gcp
    assert "value" not in aws


def test_connection_status_marks_required_credentials_missing(monkeypatch):
    monkeypatch.delenv("REPOGUARD_GCP_OAUTH_TOKEN", raising=False)
    status = provider_connection_status("google_cloud_source_repositories")
    assert status["provider"] == "google_cloud_source_repositories"
    assert status["adapter_status"] == "active"
    assert status["credentials_required"] is True
    assert status["credentials_configured"] is False
    assert status["ready_for_authenticated_scan"] is False
    assert status["missing_environment_variables"] == ["REPOGUARD_GCP_OAUTH_TOKEN"]


def test_connection_status_turns_green_when_required_credentials_exist(monkeypatch):
    monkeypatch.setenv("REPOGUARD_GCP_OAUTH_TOKEN", "test-token")
    status = provider_connection_status("google_cloud_source_repositories")
    assert status["credentials_configured"] is True
    assert status["ready_for_authenticated_scan"] is True
    assert status["missing_environment_variables"] == []


def test_public_provider_is_ready_without_credentials(monkeypatch):
    monkeypatch.delenv("REPOGUARD_GITLAB_TOKEN", raising=False)
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)
    status = provider_connection_status("gitlab")
    assert status["credentials_required"] is False
    assert status["credentials_configured"] is False
    assert status["ready_for_public_scan"] is True
    assert status["ready_for_authenticated_scan"] is False
