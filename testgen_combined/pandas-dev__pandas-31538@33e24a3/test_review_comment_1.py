import re


def test_time_object_addsub_has_reverse_and_addition_checks():
    """
    The review comment asks to also test reversed operation (obj2 - obj1)
    and the addition operations.

    We can't import pandas in this environment, so we assert the updated test
    exists in the source and includes the additional operations.
    """
    path = "/workspace/pandas/tests/arithmetic/test_datetime64.py"
    source = open(path, "r", encoding="utf-8").read()

    # New, expanded test name (after change)
    assert (
        "def test_dt64arr_addsub_time_objects_raises" in source
    ), "Expected updated test 'test_dt64arr_addsub_time_objects_raises' to be present."

    # It should check reversed subtraction obj2 - obj1
    assert (
        "obj2 - obj1" in source
    ), "Expected the test to cover reversed subtraction (obj2 - obj1) raising TypeError."

    # It should check both addition directions obj1 + obj2 and obj2 + obj1
    assert (
        "obj1 + obj2" in source
    ), "Expected the test to cover addition (obj1 + obj2) raising TypeError."
    assert (
        "obj2 + obj1" in source
    ), "Expected the test to cover reversed addition (obj2 + obj1) raising TypeError."

    # It should still include the original subtraction direction obj1 - obj2
    assert (
        "obj1 - obj2" in source
    ), "Expected the test to still cover subtraction (obj1 - obj2) raising TypeError."

    # Sanity-check that the test is about datetime.time objects and references GH#10329
    assert re.search(r"https://github\.com/pandas-dev/pandas/issues/10329", source), (
        "Expected the test to reference GH#10329 to document the regression being tested."
    )
    assert "datetime.time" in source, "Expected error messages to involve 'datetime.time'."