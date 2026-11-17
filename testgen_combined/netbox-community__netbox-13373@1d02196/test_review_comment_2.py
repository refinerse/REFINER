import re


def test_azuread_group_assignment_uses_social_auth_pipeline_config_dict():
    """
    Verify that the Azure AD docs describe group/flag mapping via the consolidated
    SOCIAL_AUTH_PIPELINE_CONFIG dict (new behavior) rather than the older
    SOCIAL_AUTH_AZUREAD_* settings.
    """
    path = "/workspace/docs/administration/authentication/microsoft-azure-ad.md"
    source = open(path, "r", encoding="utf-8").read()

    assert "## Group Assignment" in source, "Expected the Azure AD docs to include a 'Group Assignment' section."

    # New behavior: use the consolidated config dict
    assert (
        "SOCIAL_AUTH_PIPELINE_CONFIG" in source
    ), "Expected docs to define SOCIAL_AUTH_PIPELINE_CONFIG for Azure AD group assignment configuration."

    # Old behavior removed: previously used these dedicated settings
    assert (
        "SOCIAL_AUTH_AZUREAD_USER_FLAGS_BY_GROUP" not in source
    ), "Docs should not reference SOCIAL_AUTH_AZUREAD_USER_FLAGS_BY_GROUP; mappings should live under SOCIAL_AUTH_PIPELINE_CONFIG."
    assert (
        "SOCIAL_AUTH_AZUREAD_GROUP_MAP" not in source
    ), "Docs should not reference SOCIAL_AUTH_AZUREAD_GROUP_MAP; mappings should live under SOCIAL_AUTH_PIPELINE_CONFIG."

    # Ensure the keys are present under the new dict.
    # The dict contains nested braces, so don't use a naive "{...}" regex; just assert
    # both key strings appear after the first occurrence of the dict assignment.
    start = source.find("SOCIAL_AUTH_PIPELINE_CONFIG")
    assert start != -1, "Expected to find SOCIAL_AUTH_PIPELINE_CONFIG in the document."

    tail = source[start:]
    assert (
        "'AZUREAD_USER_FLAGS_BY_GROUP'" in tail
    ), "Expected SOCIAL_AUTH_PIPELINE_CONFIG to include an 'AZUREAD_USER_FLAGS_BY_GROUP' entry."
    assert (
        "'AZUREAD_GROUP_MAP'" in tail
    ), "Expected SOCIAL_AUTH_PIPELINE_CONFIG to include an 'AZUREAD_GROUP_MAP' entry."

    # Also ensure the explanatory bullets use the unprefixed names (as in the 'after' doc)
    assert (
        "**AZUREAD_USER_FLAGS_BY_GROUP.is_staff**" in source
    ), "Expected docs to describe AZUREAD_USER_FLAGS_BY_GROUP.is_staff (without SOCIAL_AUTH_AZUREAD_ prefix)."
    assert (
        "**AZUREAD_GROUP_MAP**" in source
    ), "Expected docs to describe AZUREAD_GROUP_MAP (without SOCIAL_AUTH_AZUREAD_ prefix)."