def test_debug_challenges_message_uses_internet_wording_and_not_world_wide_web() -> None:
    """
    Verify the debug-challenges prompt wording was updated consistently:
    it should say "internet" (not "world wide web") in the HTTP-01 help text.
    """
    source = open("/workspace/certbot/certbot/_internal/auth_handler.py", encoding="utf-8").read()

    assert "world wide web" not in source, (
        'Debug challenge message should not use the old phrase "world wide web"; '
        'it should be updated to "internet" consistently.'
    )

    # In the fixed code, the string is split across literals:
    # "accessible from the " + "internet ..."
    assert "accessible from the " in source and "internet and return the value mentioned" in source, (
        "Expected updated debug challenge wording for HTTP-01 to mention "
        '"accessible from the internet and return the value mentioned".'
    )