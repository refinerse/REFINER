AUTH_HANDLER_PATH = "/workspace/certbot/certbot/_internal/auth_handler.py"


def test_debug_challenges_message_uses_internet_not_world_wide_web():
    """
    Review change: in the debug challenges message, replace the user-facing phrase
    "world wide web" with "internet".
    """
    source = open(AUTH_HANDLER_PATH, "r", encoding="utf-8").read()

    assert "world wide web" not in source, (
        'The debug challenges prompt should avoid "world wide web" and use "internet" instead.'
    )

    # In the fixed code, "internet" appears inside a split string literal:
    #   "The following URLs should be accessible from the "
    #   "internet and return the value mentioned:\n"
    # So we check for that exact combined message (independent of runtime concatenation).
    expected_split_literal = (
        "The following URLs should be accessible from the "
        "\"\n                           \"internet and return the value mentioned:\\n\""
    )
    assert expected_split_literal in source, (
        "Expected the debug challenges prompt to contain the exact split string literal "
        '...accessible from the " + "internet... used in the corrected implementation.'
    )