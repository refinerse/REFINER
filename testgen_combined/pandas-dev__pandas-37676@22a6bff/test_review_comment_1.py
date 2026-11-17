import inspect

import pandas.tests.series.indexing.test_setitem as mod


def test_review_requested_loc_case_and_numeric_fixture_present():
    """
    The review requested replicating the `.loc` boolean-mask setitem case and
    expanding coverage to "any_numeric_dtype" (nullable ints + Float EA).

    We verify that the updated test method exists and that its source includes:
    - `.loc[...] =` assignment (LHS)
    - `any_numeric_dtype` fixture usage
    - the original `ser[mask] =` case
    """
    cls = mod.TestSetitemBooleanMask
    assert hasattr(
        cls, "test_setitem_boolean_nullable_int_types"
    ), (
        "Expected the reviewed test 'test_setitem_boolean_nullable_int_types' to be "
        "present on TestSetitemBooleanMask (added in response to the review comment)."
    )

    fn = cls.test_setitem_boolean_nullable_int_types
    src = inspect.getsource(fn)

    assert "any_numeric_dtype" in src, (
        "Reviewed test should use the 'any_numeric_dtype' fixture to cover nullable "
        "integer dtypes and Float extension dtypes."
    )
    assert "ser[ser > 6] =" in src, (
        "Reviewed test should still include the plain boolean mask assignment "
        "case `ser[mask] = ...`."
    )
    assert "ser.loc[ser > 6] =" in src, (
        "Reviewed test must replicate the `.loc` boolean mask setitem case on the LHS: "
        "`ser.loc[mask] = ...` (this was the key review request)."
    )