from product_catalog import PRODUCTS, get_product
from provenance import build_attestation, build_provenance, canonical_result_hash


def test_product_catalog_launch_prices_and_roles():
    expected = {
        "repo_preflight": "0.00",
        "verify_commit": "0.01",
        "safe_to_ship": "0.03",
        "repo_scan": "0.07",
        "explain_findings": "0.10",
        "attest_scan": "0.15",
    }
    assert {k: v.price_usd for k, v in PRODUCTS.items()} == expected
    assert get_product("repo_scan").includes_safe_to_ship is True
    assert get_product("safe_to_ship").returns_full_findings is False


def test_product_catalog_has_stable_machine_endpoints():
    expected = {
        "repo_preflight": "/v1/repoguard/preflight",
        "verify_commit": "/v1/repoguard/verify",
        "safe_to_ship": "/v1/repoguard/safe-to-ship",
        "repo_scan": "/v1/repoguard/scan",
        "explain_findings": "/v1/repoguard/explain",
        "attest_scan": "/v1/repoguard/attest",
    }
    assert {k: v.endpoint for k, v in PRODUCTS.items()} == expected


def test_result_hash_is_stable_for_equivalent_json_ordering():
    a = {"status": "SAFE_TO_SHIP", "score": 100, "findings": []}
    b = {"findings": [], "score": 100, "status": "SAFE_TO_SHIP"}
    assert canonical_result_hash(a) == canonical_result_hash(b)


def test_result_hash_ignores_ephemeral_scan_time():
    a = {"status": "SAFE_TO_SHIP", "score": 100, "findings": [], "scanTime": "2026-08-21T00:00:00Z"}
    b = {"status": "SAFE_TO_SHIP", "score": 100, "findings": [], "scanTime": "2026-08-21T00:00:05Z"}
    assert canonical_result_hash(a) == canonical_result_hash(b)


def test_provenance_is_commit_and_version_bound():
    result = {"status": "SAFE_TO_SHIP", "score": 100, "findings": []}
    p = build_provenance(
        provider="github",
        repository="owner/repo",
        repository_url="https://github.com/owner/repo",
        commit_sha="abc123",
        result=result,
        timestamp="2026-08-21T00:00:00Z",
    )
    assert p["source_provider"] == "github"
    assert p["repository"] == "owner/repo"
    assert p["commit_sha"] == "abc123"
    assert p["scanner_version"]
    assert p["ruleset_version"]
    assert p["adapter_version"] == "github-1.0.0"
    assert p["safe_to_ship"] is True
    assert p["result_hash"].startswith("sha256:")
    assert p["scan_id"].startswith("rg_")


def test_attestation_hash_is_stable_and_scan_bound():
    provenance = {
        "scan_id": "rg_abc",
        "source_provider": "github",
        "repository": "owner/repo",
        "commit_sha": "abc123",
        "scanner_version": "1.0.0",
        "ruleset_version": "1.0.0",
        "adapter_version": "github-1.0.0",
        "result_hash": "sha256:deadbeef",
        "safe_to_ship": True,
        "timestamp": "2026-08-21T00:00:00Z",
    }
    a = build_attestation(provenance)
    b = build_attestation(dict(provenance))
    assert a["attestation_id"] == b["attestation_id"]
    assert a["attestation_hash"] == b["attestation_hash"]
    assert a["attestation_hash"].startswith("sha256:")
