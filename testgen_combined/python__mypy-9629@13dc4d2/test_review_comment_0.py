import re

import mypy.checkexpr


def test_is_valid_keyword_var_arg_accepts_dict_nothing_nothing_mapping() -> None:
    """
    Regression test for kwargs inference/context tweak:

    The "before" version used Mapping[str, Any] as a context for **kwargs expressions,
    which can cause dict literals to be inferred as dict[<nothing>, <nothing>] in some
    situations. The fix makes mypy accept Mapping[Uninhabited, Uninhabited] as a valid
    **kwargs argument type (see is_valid_keyword_var_arg).

    This test checks for that acceptance by inspecting the implementation in a way that
    won't crash on either version.
    """
    src = open("/workspace/mypy/checkexpr.py", "r", encoding="utf-8").read()

    # Extract the body of ExpressionChecker.is_valid_keyword_var_arg (simple regex, no AST).
    m = re.search(
        r"def is_valid_keyword_var_arg\(self, typ: Type\) -> bool:\n(?P<body>(?:\s+.*\n)+?)\n\s+def has_member\(",
        src,
    )
    assert m is not None, "Could not locate ExpressionChecker.is_valid_keyword_var_arg in /workspace/mypy/checkexpr.py"
    body = m.group("body")

    assert "UninhabitedType" in body, (
        "Expected is_valid_keyword_var_arg to accept Mapping[UninhabitedType(), UninhabitedType()] "
        "as valid **kwargs (to avoid false negatives caused by dict[<nothing>, <nothing>] inference). "
        "This should be present after the fix, and absent before it."
    )