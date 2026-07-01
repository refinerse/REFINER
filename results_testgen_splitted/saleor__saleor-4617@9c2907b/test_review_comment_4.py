import re


def test_send_password_reset_email_uses_recipient_email_param_name():
    source = open("/workspace/saleor/account/emails.py", "r", encoding="utf-8").read()

    # Style requirement from review: use `recipient_email` for consistency.
    # We enforce that the Celery task `send_password_reset_email` uses the parameter
    # name `recipient_email` (not `recipient`) in its function signature.
    pattern = re.compile(
        r"@app\.task\s*\n\s*def\s+send_password_reset_email\s*\(\s*context\s*,\s*recipient_email\s*,\s*user_id\s*\)\s*:",
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "Expected `send_password_reset_email` task signature to use parameter name "
        "`recipient_email` for consistency (i.e. "
        "`def send_password_reset_email(context, recipient_email, user_id):`). "
        "The current implementation does not match this."
    )