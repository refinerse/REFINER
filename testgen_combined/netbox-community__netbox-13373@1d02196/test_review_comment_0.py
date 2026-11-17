import re


def test_authfailed_exception_removed_as_unused():
    """
    The review comment asks whether the newly added AuthFailed exception is used anywhere.
    The addressed change removes the unused AuthFailed class entirely.

    This test enforces that AuthFailed is not defined in authentication.py.
    """
    source = open("/workspace/netbox/netbox/authentication.py", "r", encoding="utf-8").read()

    assert "class AuthFailed" not in source, (
        "authentication.py should not define an unused AuthFailed exception. "
        "The review requested verifying usage, and the addressed change removes this class."
    )

    # Extra safety: ensure the removed block didn't just get renamed/aliased in a trivial way.
    # We only care that AuthFailed itself isn't present.
    assert not re.search(r"\bAuthFailed\b", source), (
        "authentication.py should not reference AuthFailed anywhere; it should be removed if unused."
    )