import re


def test_win_domain_user_no_debug_csharp_pinvoke_leftovers():
    """
    The review comment indicates the old debugging C# P/Invoke block for LogonUser
    should be removed. The fixed version uses the shared Ansible.AccessToken CSharpUtil
    and calls TokenUtil::LogonUser instead of embedding Add-Type C# code and manual
    token/password pointer handling.
    """
    source = open("/workspace/lib/ansible/modules/windows/win_domain_user.ps1", encoding="utf-8").read()

    # AFTER: should declare requirement on Ansible.AccessToken CSharpUtil
    assert (
        "#AnsibleRequires -CSharpUtil Ansible.AccessToken" in source
    ), "win_domain_user.ps1 should require the shared Ansible.AccessToken CSharpUtil (added in the fix)."

    # AFTER: should use the TokenUtil wrapper instead of embedded P/Invoke + Add-Type
    assert (
        "[Ansible.AccessToken.TokenUtil]::LogonUser" in source
    ), "win_domain_user.ps1 should call Ansible.AccessToken.TokenUtil::LogonUser (new implementation)."

    # BEFORE: embedded debugging leftovers we must not have anymore
    forbidden_patterns = [
        r"Add-Type\s+-TypeDefinition\s+\$platform_util",
        r"\[DllImport\(\"advapi32\.dll\"",
        r"class\s+WinUserPInvoke",
        r"Marshal\.SecureStringToGlobalAllocUnicode",
        r"CloseHandle\(tokenHandle\)",
        r"if\s*\(\s*returnValue\s*\|\|\s*!\(\s*tokenHandle\s*==\s*IntPtr\.Zero\s*\)\s*\)",
        r"0x00000006,\s*//\s*ERROR_INVALID_HANDLE",
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, source), (
            "win_domain_user.ps1 still contains the old embedded/debug C# P/Invoke credential test "
            f"implementation (matched pattern: {pat}). This should have been removed."
        )