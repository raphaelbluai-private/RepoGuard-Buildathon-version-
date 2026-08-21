from commerce_contracts import provider_capabilities, remediation_view, safe_to_ship_view


def test_provider_contract_preserves_original_multi_source_scope():
    caps = provider_capabilities()
    assert caps["github"]["status"] == "active"
    for provider in ["gitlab", "bitbucket", "azure_devops", "gitea", "codeberg", "aws_codecommit"]:
        assert provider in caps


def test_safe_to_ship_view_excludes_full_findings():
    result = {
        "status": "SHIP_BLOCKED",
        "score": 42,
        "findings": [
            {"id": "f1", "severity": "critical", "shortExplanation": "secret"},
            {"id": "f2", "severity": "low", "shortExplanation": "docs"},
        ],
    }
    provenance = {"scan_id": "rg_1", "result_hash": "sha256:x", "commit_sha": "abc"}
    view = safe_to_ship_view(result, provenance)
    assert view["safe_to_ship"] is False
    assert view["blocking_findings"] == 1
    assert "findings" not in view


def test_remediation_view_maps_findings_to_deterministic_actions():
    result = {
        "findings": [{
            "id": "f1",
            "ruleId": "ENV_SECRET",
            "severity": "critical",
            "shortExplanation": "Committed secret",
            "howToFix": "Remove it",
            "fixPlan": ["Rotate key", "Delete secret", "Re-scan"],
        }]
    }
    view = remediation_view(result, "rg_1")
    assert view["scan_id"] == "rg_1"
    assert view["remediation"][0]["finding_id"] == "f1"
    assert view["remediation"][0]["verification"] == "Re-scan"
