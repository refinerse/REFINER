import re


def test_stepfunctions_utils_does_not_define_duplicate_tokenize_item_and_has_return_annotation():
    source_path = "/workspace/localstack-core/localstack/services/stepfunctions/stepfunctions_utils.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # The review change moved the duplicate helper out of this module.
    # Before: this file defined `def tokenize_item(item: str) -> str:`
    # After: it should be removed.
    assert (
        "def tokenize_item(" not in source
    ), "stepfunctions_utils.py should not define tokenize_item anymore (should be moved to shared utils to avoid duplication)"

    # Additionally, the updated code annotates the function return type explicitly.
    # Before: `max_results_upper_limit: int = 1000,\n):`
    # After:  `max_results_upper_limit: int = 1000,\n) -> None:`
    pattern = re.compile(
        r"def assert_pagination_parameters_valid\([\s\S]*?\)\s*->\s*None\s*:",
        re.MULTILINE,
    )
    assert pattern.search(
        source
    ), "assert_pagination_parameters_valid should have an explicit '-> None' return annotation"