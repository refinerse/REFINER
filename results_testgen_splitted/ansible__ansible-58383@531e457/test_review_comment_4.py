import re

import pytest


PS1_PATH = "/workspace/lib/ansible/modules/windows/win_domain_user.ps1"


def test_password_credential_check_does_not_reset_changed_to_false():
    """
    Regression test for review comment:

    When checking whether credentials already match (update_password=when_changed),
    the module must not explicitly set $result.changed = $false (or
    $result.password_updated = $false), because that can overwrite an earlier
    $true change flag from user creation or other updates.

    The "after" code fixes this by using an implicit "no changes" default and
    only setting changed/password_updated to $true when a password change occurs.
    """
    source = open(PS1_PATH, encoding="utf-8").read()

    # BEFORE code had an explicit reset inside the credential-match branch:
    #   If ($test_new_credentials -and ($update_password -ne "always")) {
    #       $result.password_updated = $false
    #       $result.changed = $false
    #   }
    #
    # AFTER code does not contain such assignments and only sets $true on change.
    reset_branch_pattern = re.compile(
        r"If\s*\(\s*\$test_new_credentials\s*-and\s*\(\s*\$update_password\s*-ne\s*\"always\"\s*\)\s*\)\s*"
        r"\{\s*"
        r"\$result\.password_updated\s*=\s*\$false\s*"
        r"\$result\.changed\s*=\s*\$false\s*"
        r"\}",
        re.IGNORECASE | re.DOTALL,
    )

    assert not reset_branch_pattern.search(source), (
        "win_domain_user.ps1 must not explicitly reset $result.changed/$result.password_updated "
        "to $false when credentials already match (update_password != 'always'); "
        "doing so can overwrite earlier $true change flags. Only set these fields "
        "to $true when an actual change occurs."
    )