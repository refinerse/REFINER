import re


def test_azuread_map_groups_has_error_handling_and_no_url_reassignment():
    """
    The review requires:
    1) Error handling around Microsoft Graph API calls (try/except with contextual logging).
    2) Avoid declaring `url` multiple times; pass strings directly to requests.get().
    """
    source = open("/workspace/netbox/netbox/authentication.py", "r", encoding="utf-8").read()

    # Ensure we're examining the right function and it's present
    assert "def azuread_map_groups" in source, "azuread_map_groups() must exist in authentication.py"

    # 1) Verify that error handling was added (before code had no try/except in this function)
    # Check for the specific contextual error log introduced in the fix.
    assert (
        "Azure AD group mapping error getting groups for user" in source
        or "Azure AD group mapping error getting groups json response" in source
    ), (
        "azuread_map_groups() should catch fatal errors from Microsoft Graph requests and log context for the user "
        "(expected contextual 'Azure AD group mapping error ...' logging)."
    )

    # 2) Verify we no longer assign to a local variable named `url` in azuread_map_groups (before did twice).
    # We use a simple string/regex check rather than importing/AST.
    # This is intentionally strict to ensure the 'before' version fails reliably.
    assert not re.search(r"(?m)^\s*url\s*=\s*", source), (
        "azuread_map_groups() should avoid declaring/reassigning `url` and instead pass URLs directly to requests.get(). "
        "Found a `url = ...` assignment in authentication.py."
    )