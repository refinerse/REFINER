import re


def test_test_credential_uses_access_token_util_instead_of_manual_marshal_error():
    """
    Regression test for review comment:
    The old implementation called Marshal.GetLastWin32Error() only after CloseHandle(),
    which can overwrite the last Win32 error and result in always/incorrectly returning 0.

    The fix replaces the custom P/Invoke + GetLastWin32Error path with Ansible.AccessToken,
    which preserves/propagates the correct error information via Win32Exception.
    """
    path = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"
    source = open(path, encoding="utf-8").read()

    # AFTER should declare the CSharp util and use TokenUtil::LogonUser (new behavior).
    assert "#AnsibleRequires -CSharpUtil Ansible.AccessToken" in source, (
        "Expected win_domain_user.ps1 to require Ansible.AccessToken C# util, indicating the "
        "fixed implementation that avoids relying on Marshal.GetLastWin32Error after CloseHandle."
    )
    assert "[Ansible.AccessToken.TokenUtil]::LogonUser" in source, (
        "Expected Test-Credential to call Ansible.AccessToken.TokenUtil::LogonUser, which "
        "ensures the correct Win32 error is captured/raised rather than being overwritten."
    )

    # BEFORE used Marshal.GetLastWin32Error() + CloseHandle(tokenHandle) pattern.
    # Ensure the fragile pattern is no longer present.
    assert "Marshal.GetLastWin32Error()" not in source, (
        "Test-Credential should not use Marshal.GetLastWin32Error(); the old approach could "
        "read an overwritten last error (e.g., after CloseHandle succeeds)."
    )

    # Also ensure the old inline C# P/Invoke class isn't present anymore.
    assert "public class WinUserPInvoke" not in source, (
        "Expected the old WinUserPInvoke inline C# implementation to be removed in favor of "
        "Ansible.AccessToken, preventing incorrect last-error handling."
    )

    # Sanity: fixed code should handle Win32Exception based on NativeErrorCode.
    assert re.search(r"catch\s+\[Ansible\.AccessToken\.Win32Exception\]", source), (
        "Expected Test-Credential to catch Ansible.AccessToken.Win32Exception and inspect "
        "NativeErrorCode, matching the corrected error-handling approach."
    )