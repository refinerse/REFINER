import re


def test_azuread_map_groups_uses_hasattr_for_pipeline_config_guard():
    """
    The review comment requests using:
        if not hasattr(settings, "SOCIAL_AUTH_AZUREAD_USER_FLAGS_BY_GROUP"):
    (i.e., a hasattr()-based presence check rather than getattr(..., False) truthiness)
    for guarding configuration access.

    Since we cannot import Django modules here, enforce this via source inspection.
    This test is designed to fail on the "before" code (which uses getattr(..., False))
    and pass on the "after" code (which uses hasattr(settings, "...") for the config guard).
    """
    source = open("/workspace/netbox/netbox/authentication.py").read()

    # We expect the updated implementation to guard config existence using hasattr()
    # (now via SOCIAL_AUTH_PIPELINE_CONFIG, which was introduced in the "after" code).
    assert (
        'if not hasattr(settings, "SOCIAL_AUTH_PIPELINE_CONFIG")' in source
    ), (
        "Expected azuread_map_groups to guard configuration using hasattr(settings, "
        '"SOCIAL_AUTH_PIPELINE_CONFIG") (presence check), rather than relying on getattr(..., False) truthiness.'
    )

    # Ensure the old pattern is not present (it would incorrectly treat an empty dict/list as "undefined").
    old_patterns = [
        'getattr(settings, "SOCIAL_AUTH_AZUREAD_USER_FLAGS_BY_GROUP", False)',
        'getattr(settings, "SOCIAL_AUTH_AZUREAD_GROUP_MAP", False)',
    ]
    assert not any(p in source for p in old_patterns), (
        "Found legacy getattr(..., False) truthiness checks for AzureAD mapping settings. "
        "These should be replaced by presence checks (hasattr or dict key existence) to avoid "
        "treating empty-but-defined configuration as undefined."
    )

    # Also assert that the azuread_map_groups function exists in the file (sanity check).
    assert re.search(r"\ndef\s+azuread_map_groups\s*\(", source), (
        "Expected azuread_map_groups() to exist in /workspace/netbox/netbox/authentication.py."
    )