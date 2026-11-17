import re

import pytest


WIN_DOMAIN_USER_PS1 = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"


def test_test_credential_uses_string_password_not_intptr_and_no_manual_securestring_marshalling():
    """
    The review change replaces a custom C# PInvoke signature that took an IntPtr password
    (with manual SecureString -> unmanaged ptr conversion) with a string password approach
    (via Ansible.AccessToken TokenUtil::LogonUser).

    This test asserts the module no longer contains the old risky/complex patterns:
      - LogonUser(..., IntPtr password, ...)
      - Marshal.SecureStringToGlobalAllocUnicode / ZeroFreeGlobalAllocUnicode
      - ConvertTo-SecureString used for TestCredential invocation
    and that it does use the new AccessToken helper.
    """
    source = open(WIN_DOMAIN_USER_PS1, encoding="utf-8").read()

    # Positive check for the intended replacement path (after-code behavior).
    assert (
        "Ansible.AccessToken.TokenUtil" in source and "::LogonUser(" in source
    ), "Expected win_domain_user.ps1 to use Ansible.AccessToken.TokenUtil::LogonUser for credential testing."

    # The old implementation had a PInvoke signature with IntPtr password.
    assert (
        re.search(r"LogonUser\s*\(\s*String\s+username\s*,\s*String\s+domain\s*,\s*IntPtr\s+password", source)
        is None
    ), "Expected the old PInvoke signature 'LogonUser(..., IntPtr password, ...)' to be removed."

    # The old implementation manually marshaled SecureString to unmanaged memory.
    assert (
        "Marshal.SecureStringToGlobalAllocUnicode" not in source
    ), "Expected manual SecureString marshaling (Marshal.SecureStringToGlobalAllocUnicode) to be removed."
    assert (
        "Marshal.ZeroFreeGlobalAllocUnicode" not in source
    ), "Expected manual unmanaged password cleanup (Marshal.ZeroFreeGlobalAllocUnicode) to be removed."

    # The old PowerShell call site converted the plaintext password to SecureString for TestCredential.
    assert (
        re.search(r"::TestCredential\([^)]*ConvertTo-SecureString\s+\$Password", source, re.IGNORECASE)
        is None
    ), "Expected Test-Credential to no longer pass a SecureString created from plaintext via ConvertTo-SecureString."