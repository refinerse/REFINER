import re


def test_maybe_cast_result_dtype_uses_elif_for_second_branch():
    source = open("/workspace/pandas/core/dtypes/cast.py", "r", encoding="utf-8").read()

    # We want to ensure the second condition in maybe_cast_result_dtype is an
    # `elif`, not a separate `if` (per review comment "can be elif").
    #
    # This is a source-level behavior check because importing pandas is broken
    # in this environment (pre-flight import error).
    pattern = re.compile(
        r"def maybe_cast_result_dtype\(dtype: DtypeObj, how: str\) -> DtypeObj:"
        r"(?s).*?"
        r"\n\s*if how in \[\"add\", \"cumsum\", \"sum\"\] and \(dtype == np\.dtype\(np\.bool\)\):"
        r"\n\s*return np\.dtype\(np\.int64\)"
        r"\n\s*elif how in \[\"add\", \"cumsum\", \"sum\"\] and isinstance\(dtype, \w*BooleanDtype\):",
        re.MULTILINE,
    )

    assert pattern.search(source), (
        "Expected maybe_cast_result_dtype to use `elif` for the BooleanDtype branch "
        "immediately after the bool->int64 branch. This ensures the two branches are "
        "mutually exclusive and matches the review comment 'can be elif'."
    )