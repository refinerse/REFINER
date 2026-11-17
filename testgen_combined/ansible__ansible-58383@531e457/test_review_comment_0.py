import re


def test_test_credential_does_not_expose_provider_or_logon_type_params():
    """
    Style requirement from review: don't expose both provider and logon type.
    Concretely, Test-Credential should not accept LOGON32 provider/type params.
    """
    path = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"
    source = open(path, encoding="utf-8").read()

    # Ensure we're checking the right function block.
    assert "Function Test-Credential" in source, (
        "Expected win_domain_user.ps1 to define Function Test-Credential; "
        "test relies on inspecting its parameter list."
    )

    # BEFORE code exposed $LOGON32_PROVIDER and $LOGON32_LOGON_TYPE in param().
    # AFTER code removes these and uses the module CSharp util wrapper instead.
    assert "$LOGON32_PROVIDER" not in source and "$LOGON32_LOGON_TYPE" not in source, (
        "Test-Credential should not expose LOGON32 provider/logon type parameters; "
        "they complicate the public surface. Remove $LOGON32_PROVIDER and "
        "$LOGON32_LOGON_TYPE from the function param() list."
    )


def test_module_uses_access_token_csharp_util_instead_of_inline_pinvoke():
    """
    Companion check to ensure the style refactor happened:
    module should depend on Ansible.AccessToken C# util rather than embedding
    a custom WinUserPInvoke implementation.
    """
    path = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"
    source = open(path, encoding="utf-8").read()

    assert "#AnsibleRequires -CSharpUtil Ansible.AccessToken" in source, (
        "Expected module to declare dependency on Ansible.AccessToken via "
        "#AnsibleRequires -CSharpUtil Ansible.AccessToken."
    )

    assert "class WinUserPInvoke" not in source, (
        "Module should not embed an inline C# P/Invoke helper (WinUserPInvoke); "
        "use the shared Ansible.AccessToken util instead."
    )

    # Basic sanity: call should use TokenUtil::LogonUser with string args for type/provider.
    assert re.search(r"\[Ansible\.AccessToken\.TokenUtil\]::LogonUser\(", source), (
        "Expected Test-Credential to call [Ansible.AccessToken.TokenUtil]::LogonUser(...)."
    )