import re


def test_authenticator_email_models_no_longer_defines_get_template_choices():
    """
    Review comment requests refactor of duplicated template-choice logic.
    Observable change: authentik/stages/authenticator_email/models.py should no longer
    define its own get_template_choices() helper (it was removed in the 'after' code).
    """
    source = open("/workspace/authentik/stages/authenticator_email/models.py", "r", encoding="utf-8").read()

    has_func = re.search(r"(?m)^\s*def\s+get_template_choices\s*\(", source) is not None

    assert (
        not has_func
    ), "models.py should not define get_template_choices(); duplicated template-choice logic should be refactored out (function removed)."