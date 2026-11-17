import inspect

import pandas.tests.frame.methods.test_isin as mod


def test_review_change_parametrized_category_isin_test_present_and_old_removed():
    """
    The review comment asked to avoid two identical expected objects by using a
    single expected and sharing the assertions via parametrization.

    Verify that the new parametrized test exists and the old duplicate-expected
    test name no longer exists in the module.
    """
    assert hasattr(
        mod.TestDataFrameIsIn, "test_isin_category_frame"
    ), "Expected new parametrized test 'test_isin_category_frame' to exist after the review change."

    assert not hasattr(
        mod.TestDataFrameIsIn, "test_isin_against_categoryDataframe"
    ), (
        "Old test 'test_isin_against_categoryDataframe' should be removed/renamed after the review change "
        "(it duplicated identical expected1/expected2)."
    )

    src = inspect.getsource(mod.TestDataFrameIsIn.test_isin_category_frame)
    assert "parametrize" in src, (
        "New test should be parametrized over values (DataFrame/Series category) "
        "to reuse a single 'expected' for both assertions."
    )
    assert "expected =" in src and "expected1" not in src and "expected2" not in src, (
        "New test should use a single variable named 'expected' and not keep duplicate "
        "'expected1'/'expected2' variables."
    )