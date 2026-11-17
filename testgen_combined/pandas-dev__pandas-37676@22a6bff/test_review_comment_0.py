import inspect
import re

import pandas.tests.series.indexing.test_setitem as mod


def test_style_review_applied_setitem_boolean_nullable_int_types_present():
    """
    Style review required renaming the newly added test from
    `test_setitem_boolean_ea_type` (with 1-letter var `s` and explicit Int64 array)
    to `test_setitem_boolean_nullable_int_types` (with `ser` and parametrization).

    This test enforces that the old test name is gone and the new one exists.
    """
    cls = mod.TestSetitemBooleanMask

    assert not hasattr(
        cls, "test_setitem_boolean_ea_type"
    ), "Expected old test name 'test_setitem_boolean_ea_type' to be removed after style review."

    assert hasattr(
        cls, "test_setitem_boolean_nullable_int_types"
    ), "Expected new test name 'test_setitem_boolean_nullable_int_types' to exist after style review."

    # Light sanity check that new test uses `ser` variable name (avoid 1-letter names).
    src = inspect.getsource(getattr(cls, "test_setitem_boolean_nullable_int_types"))
    assert re.search(r"\bser\s*=", src), (
        "Expected the updated test to use a non-1-letter variable name like 'ser'. "
        "Could not find an assignment to 'ser' in the test source."
    )