import re


def test_test_credential_does_not_check_token_handle_value():
    """
    Review comment: "No need to check the handle value, just base it off the LogonUser return value."

    The fixed code should not include logic that treats a non-zero handle as success
    independent of the LogonUser() return value.
    """
    source = open("/workspace/lib/ansible/modules/windows/win_domain_user.ps1", encoding="utf-8").read()

    # BEFORE code had this (or equivalent) logic in the embedded C#:
    #   if (returnValue || !(tokenHandle == IntPtr.Zero)) { return true; }
    #
    # AFTER code removes this handle-based success check entirely.
    forbidden_patterns = [
        r"returnValue\s*\|\|\s*!\s*\(\s*tokenHandle\s*==\s*IntPtr\.Zero\s*\)",
        r"returnValue\s*\|\|\s*tokenHandle\s*!=\s*IntPtr\.Zero",
    ]

    assert not any(re.search(p, source) for p in forbidden_patterns), (
        "Test-Credential should not consider the token handle value when deciding success; "
        "success must be based on the LogonUser return value (plus explicit Win32 error handling). "
        "Found a handle-based success check like `returnValue || tokenHandle != IntPtr.Zero`."
    )