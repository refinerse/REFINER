import inspect

import pandas.tests.frame.methods.test_isin as mod


def test_isin_test_name_uses_snake_case_not_camelcase():
    """
    Enforce review comment: don't use camelcase in test name.

    Before: test_isin_against_categoryDataframe (camelcase 'Dataframe')
    After:  test_isin_category_frame (snake_case)
    """
    cls = mod.TestDataFrameIsIn

    assert hasattr(
        cls, "test_isin_category_frame"
    ), "Expected snake_case test method 'test_isin_category_frame' to exist."

    assert not hasattr(
        cls, "test_isin_against_categoryDataframe"
    ), (
        "CamelCase test method 'test_isin_against_categoryDataframe' should not exist; "
        "rename to 'test_isin_category_frame'."
    )

    # Extra guard: ensure no test method name contains the specific camelcase fragment.
    camelcase = [
        name
        for name, _ in inspect.getmembers(cls, predicate=callable)
        if name.startswith("test_") and "categoryDataframe" in name
    ]
    assert camelcase == [], (
        "Found camelcase 'categoryDataframe' in test method names: "
        f"{camelcase}. Use snake_case instead."
    )