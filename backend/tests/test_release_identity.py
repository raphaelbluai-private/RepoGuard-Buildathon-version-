import pytest
from release_identity import canonical_hash, release_manifest, reconcile_runtime

SHA = "a" * 40
DIGEST = "sha256:" + "b" * 64

def make_manifest():
    return release_manifest(source_sha=SHA, image_digest=DIGEST,
                            configuration={"network": "eip155:84532", "public_preview": True},
                            build_id="ci-290")

def test_deterministic_release_manifest():
    assert make_manifest() == make_manifest()

def test_identity_match_is_not_launch_authorization():
    m = make_manifest()
    result = reconcile_runtime(m, observed_source_sha=SHA,
        observed_image_digest=DIGEST, observed_configuration_hash=m["configuration_hash"])
    assert result["status"] == "IDENTITY_MATCH"
    assert result["release_authorized"] is False

@pytest.mark.parametrize("field", ["source_sha", "image_digest", "configuration_hash"])
def test_missing_or_mismatched_identity_fails_closed(field):
    m = make_manifest()
    values = {"observed_source_sha": SHA, "observed_image_digest": DIGEST,
              "observed_configuration_hash": m["configuration_hash"]}
    values["observed_" + field] = None
    result = reconcile_runtime(m, **values)
    assert result["status"] == "BLOCKED_UNKNOWN_OR_DRIFT"
    assert field in result["mismatches"]

def test_secret_config_keys_rejected():
    with pytest.raises(ValueError, match="secret material"):
        release_manifest(source_sha=SHA, image_digest=DIGEST,
                         configuration={"api_key": "sensitive"}, build_id="ci")

def test_invalid_source_and_image_rejected():
    with pytest.raises(ValueError):
        release_manifest(source_sha="main", image_digest=DIGEST,
                         configuration={}, build_id="ci")
    with pytest.raises(ValueError):
        release_manifest(source_sha=SHA, image_digest="latest",
                         configuration={}, build_id="ci")
