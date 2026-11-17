import re


def test_token_expiry_uses_timedelta_string_format_and_validator():
    source = open("/workspace/authentik/stages/authenticator_email/models.py", encoding="utf-8").read()

    # Ensure token_expiry is declared as a TextField with a timedelta string default + validator.
    # This matches the consistency change requested in the review comment.
    assert "token_expiry" in source, "Expected AuthenticatorEmailStage to define a token_expiry field."

    assert "models.TextField" in source, (
        "Expected token_expiry to be a TextField to allow timedelta string format "
        "(e.g. 'minutes=30') instead of an IntegerField."
    )

    assert "timedelta_string_validator" in source, (
        "Expected token_expiry to use timedelta_string_validator for consistent duration parsing."
    )

    # Check the token_expiry field block contains the expected default format.
    # Use a regex so formatting/whitespace doesn't make the test brittle.
    pattern = re.compile(
        r"token_expiry\s*=\s*models\.TextField\(\s*"
        r"(?:.|\n)*?default\s*=\s*[\"']minutes=30[\"']\s*,"
        r"(?:.|\n)*?validators\s*=\s*\[\s*timedelta_string_validator\s*\]\s*,",
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "Expected token_expiry to be declared as models.TextField(default='minutes=30', "
        "validators=[timedelta_string_validator], ...) to use the standard timedelta string format."
    )

    # Negative guard: the old implementation should not be present.
    assert "token_expiry = models.IntegerField" not in source, (
        "token_expiry should no longer be an IntegerField (minutes-only); it should use "
        "a TextField with timedelta_string_validator."
    )