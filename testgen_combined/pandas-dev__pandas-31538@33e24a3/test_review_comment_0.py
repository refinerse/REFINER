import re

import pytest


def test_review_comment_and_to_addsub_rename_and_expansion():
    """
    Functional intent of the review: rename the newly-added test from
    "..._and_..." to "..._addsub_..." and expand coverage.

    Since importing pandas' test module is not possible in this execution
    environment, we assert on the repository source file content directly.
    """
    path = "/workspace/pandas/tests/arithmetic/test_datetime64.py"
    source = open(path).read()

    # BEFORE: added a narrow test named "test_timestamp_and_time_dtype_raises"
    # AFTER: replaced by a broader "test_dt64arr_addsub_time_objects_raises"
    assert (
        "def test_dt64arr_addsub_time_objects_raises" in source
    ), "Expected the test to be renamed to use 'addsub' (per review comment) and exist."

    assert (
        "def test_timestamp_and_time_dtype_raises" not in source
    ), "Expected the old test name containing 'and' to be removed/renamed to 'addsub'."

    # Ensure expanded behavior checks are present: both + and -, and reversed operations.
    # We require these specific operation lines, which the 'before' version lacks.
    required_lines = [
        "obj1 - obj2",
        "obj2 - obj1",
        "obj1 + obj2",
        "obj2 + obj1",
    ]
    for line in required_lines:
        assert line in source, f"Expected expanded add/sub coverage to include operation: {line}"

    # Also ensure time objects are included in the invalid add/sub parametrization (moved there in after).
    assert re.search(r"test_dt64arr_add_sub_invalid[\s\S]*time\(", source), (
        "Expected datetime.time to be included among invalid add/sub operands in "
        "test_dt64arr_add_sub_invalid parameterization."
    )