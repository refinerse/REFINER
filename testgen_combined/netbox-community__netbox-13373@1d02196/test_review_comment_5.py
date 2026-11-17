import re


def test_azuread_group_mapping_no_toggle_setting_gate():
    """
    The review comment indicates we should not need a dedicated enable/disable setting.
    Instead, adding/removing the function from the social-auth pipeline should control usage.

    Therefore, azuread_map_groups should NOT be gated by a setting like
    SOCIAL_AUTH_AZUREAD_MAP_GROUP_PERMS (present in the "before" code).
    """
    source = open("/workspace/netbox/netbox/authentication.py").read()

    # Extract just the azuread_map_groups function body (best-effort, avoids full AST parsing).
    m = re.search(r"\ndef azuread_map_groups\([^\)]*\):(?P<body>.*?)(?=\n\ndef |\nclass |\Z)", source, re.S)
    assert m, "Expected to find def azuread_map_groups(...) in /workspace/netbox/netbox/authentication.py"

    body = m.group("body")

    assert "SOCIAL_AUTH_AZUREAD_MAP_GROUP_PERMS" not in body, (
        "azuread_map_groups() should not be gated by SOCIAL_AUTH_AZUREAD_MAP_GROUP_PERMS; "
        "enable/disable should be controlled by adding/removing the pipeline function."
    )