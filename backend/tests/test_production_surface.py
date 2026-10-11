from fastapi.testclient import TestClient

import commerce_app_v2


client = TestClient(commerce_app_v2.app)


def test_production_surface_does_not_expose_legacy_or_internal_routes():
    blocked = (
        ("post", "/api/scan"),
        ("post", "/api/auth/request-code"),
        ("post", "/api/demo-trigger"),
        ("get", "/api/_internal/rate-stats"),
        ("get", "/api/events"),
    )
    for method, path in blocked:
        response = (
            client.post(path, json={}) if method == "post" else client.get(path)
        )
        assert response.status_code == 404, path


def test_production_openapi_contains_only_commerce_api_routes():
    api_paths = {
        path for path in commerce_app_v2.app.openapi()["paths"] if path.startswith(("/api", "/v1"))
    }
    assert api_paths == {
        "/v1/repoguard/products",
        "/v1/repoguard/preflight",
        "/v1/repoguard/verify",
        "/v1/repoguard/safe-to-ship",
        "/v1/repoguard/scan",
        "/v1/repoguard/explain",
        "/v1/repoguard/attest",
    }


def test_authenticated_provider_is_rejected_before_network(monkeypatch):
    def must_not_run(*args, **kwargs):
        raise AssertionError("network lookup must not run")

    monkeypatch.setattr(commerce_app_v2, "repo_head_identity", must_not_run)
    preflight = client.post(
        "/v1/repoguard/preflight",
        json={"provider": "aws_codecommit", "repo": "us-east-1/demo"},
    )
    verify = client.post(
        "/v1/repoguard/verify",
        json={
            "provider": "aws_codecommit",
            "repo": "us-east-1/demo",
            "expected_commit_sha": "abc",
        },
    )
    assert preflight.json()["error"] == "PUBLIC_REPOSITORY_REQUIRED"
    assert preflight.json()["scan_available"] is False
    assert verify.status_code == 403
    assert verify.json()["detail"]["error"] == "PUBLIC_REPOSITORY_REQUIRED"
