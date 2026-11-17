import re


def test_error_message_regexes_use_join_style_for_alternations():
    """
    Style test (source-level): alternation regexes assigned to a `msg` variable
    should be built with `msg = "|".join([...])` instead of a single parenthesized
    multi-line raw string containing `|`.

    We scope this check specifically to cases where the regex contains alternation
    (`|`), since plenty of `msg = (...)` string concatenations without alternation
    are fine and exist in the file.
    """
    path = "/workspace/pandas/tests/tools/test_to_datetime.py"
    source = open(path, "r", encoding="utf-8").read()

    assert (
        'msg = "|".join(' in source
    ), "Expected at least one `msg = \"|\".join([...])` instance in the file."

    # The "before" version had patterns like:
    # msg = (
    #     r'^(...|...)$'
    # )
    #
    # The "after" version may still legitimately have `msg = (` for simple string
    # concatenation (without `|`), so only flag `msg = (` blocks that include a `|`
    # before the closing `)`.
    bad_msg_paren_with_or = re.compile(
        r"""
        msg\s*=\s*\(          # msg = (
        (?P<body>.*?)         # body (non-greedy)
        \n\s*\)               # closing paren on its own line (possibly indented)
        """,
        re.DOTALL | re.VERBOSE,
    )

    for m in bad_msg_paren_with_or.finditer(source):
        body = m.group("body")
        assert "|" not in body, (
            "Found a `msg = (` ... `)` block that contains a `|` alternation. "
            "For alternation regexes, use `msg = \"|\".join([...])` instead of a "
            "single parenthesized string."
        )