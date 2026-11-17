import re


def test_email_subject_default_is_end_user_friendly_sign_in_code():
    """
    Review requested changing the default email subject to a more end-user friendly
    value and specifically avoiding "OTP" wording. Since Django isn't available
    in this environment, assert via source inspection.
    """
    source = open("/workspace/authentik/stages/authenticator_email/models.py", encoding="utf-8").read()

    # Ensure the subject field default is updated to the requested string.
    # This should FAIL on before code (default="authentik") and PASS on after code.
    assert (
        'subject = models.TextField(default="authentik Sign-in code")' in source
    ), (
        "Expected AuthenticatorEmailStage.subject to default to "
        '"authentik Sign-in code" (end-user friendly), but it was not found in '
        "/workspace/authentik/stages/authenticator_email/models.py."
    )

    # Extra guard to ensure we didn't regress into an OTP-themed title.
    subject_default_match = re.search(
        r"subject\s*=\s*models\.TextField\(\s*default\s*=\s*(['\"])(?P<val>.+?)\1", source
    )
    assert subject_default_match, "Could not locate a models.TextField default for subject in source."
    assert (
        "OTP" not in subject_default_match.group("val")
    ), 'Subject default should not contain "OTP" to avoid confusing end users.'