import inspect

import pandas.tests.indexes.test_numeric as mod


def test_test_equals_numeric_other_index_type_is_parametrized():
    """
    The review comment asked to paramaterize the "other index type" equality checks.
    The addressed version introduces a dedicated parametrized test method:
    `test_equals_numeric_other_index_type`.

    This test asserts that the new parametrized test exists in the module and
    is marked with pytest.parametrize.
    """
    assert hasattr(
        mod.TestFloat64Index, "test_equals_numeric_other_index_type"
    ), (
        "Expected TestFloat64Index.test_equals_numeric_other_index_type to exist; "
        "this indicates the 'other index type' equals checks were refactored into "
        "a parametrized test as requested in the review."
    )

    fn = mod.TestFloat64Index.test_equals_numeric_other_index_type
    marks = getattr(fn, "pytestmark", [])
    has_parametrize = any(getattr(m, "name", None) == "parametrize" for m in marks)

    assert has_parametrize, (
        "Expected test_equals_numeric_other_index_type to be decorated with "
        "pytest.mark.parametrize, but it was not. Found source:\n\n"
        f"{inspect.getsource(fn)}"
    )