import re


def test_authenticator_email_stage_meta_verbose_name_typo_fixed():
    source = open("/workspace/authentik/stages/authenticator_email/models.py", encoding="utf-8").read()

    # Before version had a typo in verbose_name: "Email Autherenticator Stage"
    assert "Email Autherenticator Stage" not in source, (
        "Expected the typo 'Email Autherenticator Stage' to be removed from "
        "AuthenticatorEmailStage.Meta.verbose_name, but it is still present."
    )

    # Ensure AuthenticatorEmailStage.Meta.verbose_name exists and uses the correct spelling
    # ("Email Authenticator ..."), without over-constraining the exact final label.
    # After version uses: _("Email Authenticator Setup Stage")
    pattern = re.compile(
        r"class\s+AuthenticatorEmailStage\b[\s\S]*?"
        r"class\s+Meta\s*:\s*[\s\S]*?"
        r"verbose_name\s*=\s*_\(\s*[\"']Email Authenticator",
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "Expected AuthenticatorEmailStage.Meta.verbose_name to start with "
        "'Email Authenticator' (correct spelling)."
    )