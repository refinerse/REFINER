import re


def test_first_last_deprecation_message_includes_loc_guidance():
    # NOTE: Do not import dask; repository conftest/imports fail in this environment.
    source = open("/workspace/dask/dataframe/core.py", encoding="utf-8").read()

    expected_guidance = "Please create a mask and filter using .loc instead"

    def find_deprecated_message_expr(method_name: str) -> str | None:
        # Look for @_deprecated(message=...) immediately preceding def <method_name>(
        # Allow message to be a single string literal or a parenthesized implicit concat.
        pattern = (
            r"@_deprecated\(\s*message\s*=\s*(?P<msg>"
            r"(?:"
            r"\"(?:\\.|[^\"])*\""  # "..."
            r"|"
            r"\(\s*(?:\"(?:\\.|[^\"])*\"\s*)+\)"  # ("..." "..." ...)
            r")"
            r")\s*\)\s*"
            r"@derived_from\([^\)]*\)\s*"
            r"def\s+"
            + re.escape(method_name)
            + r"\s*\("
        )
        m = re.search(pattern, source, flags=re.DOTALL)
        return None if m is None else m.group("msg")

    first_msg_expr = find_deprecated_message_expr("first")
    last_msg_expr = find_deprecated_message_expr("last")

    assert first_msg_expr is not None, (
        "Expected an @_deprecated(message=...) decorator immediately above "
        "`def first(...)` in /workspace/dask/dataframe/core.py"
    )
    assert last_msg_expr is not None, (
        "Expected an @_deprecated(message=...) decorator immediately above "
        "`def last(...)` in /workspace/dask/dataframe/core.py"
    )

    assert expected_guidance in first_msg_expr, (
        "Expected `_Frame.first` deprecation message to include actionable guidance "
        f"({expected_guidance!r}), but it did not. Found message expression:\n"
        f"{first_msg_expr}"
    )
    assert expected_guidance in last_msg_expr, (
        "Expected `_Frame.last` deprecation message to include actionable guidance "
        f"({expected_guidance!r}), but it did not. Found message expression:\n"
        f"{last_msg_expr}"
    )