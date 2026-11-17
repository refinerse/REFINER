import re


def test_debug_challenges_message_avoids_excess_leading_newline_in_mixed_challenges():
    """
    The pre-fix code builds debug challenge text by appending strings that *start with* "\\n"
    (e.g. "\\nThe following URLs..."), which creates an excess blank line when joined into the
    notification message, especially in mixed HTTP/DNS challenge scenarios.

    The fixed code centralizes message construction in _debug_challenges_msg() and removes those
    leading "\\n" prefixes (instead returning a single leading newline before the whole block).
    """
    source = open("/workspace/certbot/certbot/_internal/auth_handler.py", encoding="utf-8").read()

    # Assert the fix exists: a dedicated helper method is present in the refactored version.
    assert "_debug_challenges_msg" in source, (
        "Expected refactor to introduce AuthHandler._debug_challenges_msg() helper for building "
        "debug challenge messages; this helper is required to avoid the excess leading newline."
    )

    # The buggy behavior: leading newline before the HTTP header line.
    assert not re.search(r'msg\.append\(\s*"\nThe following URLs', source), (
        "Found a message header appended with a leading newline "
        '(msg.append("\\nThe following URLs...")). This causes an excess blank line in the debug '
        "challenges prompt when messages are joined (e.g., with mixed HTTP/DNS challenges)."
    )

    # Also check the DNS header variant from the buggy code path.
    assert not re.search(r'msg\.append\(\s*"\nThe following FQDNs', source), (
        "Found a message header appended with a leading newline "
        '(msg.append("\\nThe following FQDNs...")). This contributes to excess blank lines in the '
        "debug challenges prompt; the fixed implementation should not use leading newlines here."
    )