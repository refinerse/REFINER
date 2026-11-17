import re


def test_win_domain_user_ps1_removes_domain_workaround_and_uses_access_token_util():
    """
    Structural regression test for win_domain_user.ps1:

    The pre-fix version contained a workaround line:
        $null = $Domain # Make CI-Check happy...

    The fixed version removed that workaround and instead relies on:
        #AnsibleRequires -CSharpUtil Ansible.AccessToken
    and uses:
        [Ansible.AccessToken.TokenUtil]::LogonUser(...)
    """
    path = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"
    source = open(path, encoding="utf-8").read()

    assert "$null = $Domain" not in source, (
        "win_domain_user.ps1 should not contain the '$null = $Domain' workaround; "
        "it was a CI/PSScriptAnalyzer suppression that should be removed."
    )

    assert "#AnsibleRequires -CSharpUtil Ansible.AccessToken" in source, (
        "win_domain_user.ps1 should declare the Ansible.AccessToken CSharpUtil requirement "
        "after the workaround removal."
    )

    assert re.search(r"\[Ansible\.AccessToken\.TokenUtil\]::LogonUser\(", source), (
        "win_domain_user.ps1 should use Ansible.AccessToken.TokenUtil::LogonUser() "
        "instead of embedding custom C# P/Invoke code."
    )