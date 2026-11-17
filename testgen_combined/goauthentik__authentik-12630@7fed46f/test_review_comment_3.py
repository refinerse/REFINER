import re


def test_authenticator_email_stage_removes_unused_logger():
    """
    Review comment: "Never used" referring to LOGGER = get_logger() and its import.
    Ensure authentik/stages/authenticator_email/stage.py no longer defines/uses LOGGER.
    This should fail on the old code (LOGGER present) and pass on the new code (removed).
    """
    source = open("/workspace/authentik/stages/authenticator_email/stage.py", "r", encoding="utf-8").read()

    assert (
        "from structlog.stdlib import get_logger" not in source
    ), "stage.py should not import get_logger from structlog.stdlib (it was unused)."

    assert (
        re.search(r"^\s*LOGGER\s*=\s*get_logger\(\)\s*$", source, flags=re.MULTILINE) is None
    ), "stage.py should not define LOGGER = get_logger(); LOGGER was never used."