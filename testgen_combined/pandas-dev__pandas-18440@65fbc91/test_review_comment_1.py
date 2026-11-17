import inspect

import pandas.tests.indexes.test_multi as test_multi


def test_review_comment_use_assert_index_equal():
    """
    Enforce review comment "use assert_index_equal" by checking that the
    new iterator-based MultiIndex tests use tm.assert_index_equal instead of
    `result.equals(...)` asserts.

    This is a style-only change with no runtime behavior difference, so we
    verify via source inspection of the test functions.
    """
    src_product_it = inspect.getsource(test_multi.TestMultiIndex.test_from_product_iterator)
    assert "tm.assert_index_equal" in src_product_it, (
        "Expected TestMultiIndex.test_from_product_iterator to use "
        "tm.assert_index_equal(result, expected) per review comment."
    )
    assert "equals(expected)" not in src_product_it, (
        "Expected TestMultiIndex.test_from_product_iterator to avoid "
        "`assert result.equals(expected)` and use tm.assert_index_equal instead."
    )

    src_tuples = inspect.getsource(test_multi.TestMultiIndex.test_from_tuples)
    assert "tm.assert_index_equal" in src_tuples, (
        "Expected TestMultiIndex.test_from_tuples to use tm.assert_index_equal "
        "per review comment."
    )
    assert "equals(expected)" not in src_tuples, (
        "Expected TestMultiIndex.test_from_tuples to avoid "
        "`assert result.equals(expected)` and use tm.assert_index_equal instead."
    )

    src_tuples_it = inspect.getsource(test_multi.TestMultiIndex.test_from_tuples_iterator)
    assert "tm.assert_index_equal" in src_tuples_it, (
        "Expected TestMultiIndex.test_from_tuples_iterator to use "
        "tm.assert_index_equal per review comment."
    )
    assert "equals(expected)" not in src_tuples_it, (
        "Expected TestMultiIndex.test_from_tuples_iterator to avoid "
        "`assert result.equals(expected)` and use tm.assert_index_equal instead."
    )