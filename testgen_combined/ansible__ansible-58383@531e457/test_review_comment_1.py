import re

FILE_PATH = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"


def test_test_credential_uses_access_token_util_and_not_custom_constants():
    """
    Review intent: no need to provide LOGON32_* constants/params and custom P/Invoke C# blob.
    After fix should rely on Ansible.AccessToken CSharpUtil and pass provider/logon type as-is.
    """
    source = open(FILE_PATH, encoding="utf-8").read()

    # Must use shared CSharpUtil instead of embedding a C# P/Invoke implementation.
    assert "#AnsibleRequires -CSharpUtil Ansible.AccessToken" in source, (
        "win_domain_user.ps1 should declare the Ansible.AccessToken CSharpUtil requirement "
        "instead of embedding its own LogonUser/LOGON32 constants implementation."
    )
    assert "[Ansible.AccessToken.TokenUtil]::LogonUser" in source, (
        "Test-Credential should call Ansible.AccessToken.TokenUtil::LogonUser(...) to validate "
        "credentials using Network logon type and Default provider."
    )

    # Must not expose LOGON32_PROVIDER/LOGON32_LOGON_TYPE as parameters anymore.
    assert "LOGON32_PROVIDER" not in source and "LOGON32_LOGON_TYPE" not in source, (
        "Test-Credential should not define/accept LOGON32_PROVIDER or LOGON32_LOGON_TYPE constants/params; "
        "it should always use Network logon and Default provider."
    )

    # Must not embed the old C# P/Invoke blob.
    assert "public class WinUserPInvoke" not in source, (
        "win_domain_user.ps1 should not embed a custom C# P/Invoke WinUserPInvoke helper; "
        "it should use the shared Ansible.AccessToken utility instead."
    )

    # Basic sanity check that LogonUser is called with 'Network' and 'Default' string args.
    assert re.search(r'LogonUser\([^)]*"Network"\s*,\s*"Default"\s*\)', source), (
        "Expected TokenUtil::LogonUser to be invoked with logon type 'Network' and provider 'Default'."
    )