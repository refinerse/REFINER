import re


def test_assert_pagination_parameters_valid_has_explicit_none_return_annotation():
    source_path = "/workspace/localstack-core/localstack/services/stepfunctions/stepfunctions_utils.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Verify the function definition exists
    assert (
        "def assert_pagination_parameters_valid" in source
    ), "Expected assert_pagination_parameters_valid to be defined in stepfunctions_utils.py"

    # The review asks to keep an explicit `-> None` return type annotation.
    # We check for the specific signature fragment around the closing parenthesis.
    pattern = re.compile(
        r"def\s+assert_pagination_parameters_valid\s*\([\s\S]*?\)\s*->\s*None\s*:",
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "Expected assert_pagination_parameters_valid to have an explicit return type "
        "annotation '-> None:' (documentation/type-hint clarity)."
    )