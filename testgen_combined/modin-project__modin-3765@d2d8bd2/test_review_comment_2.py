import re


def test_loc_insert_row_function_moved_out_of_loop_and_parametrized():
    """
    Functional intent of review: the helper function `_test_loc_rows` should not be
    defined inside a `for left, right in ...` loop; instead it should be defined once
    and the test should be parameterized (as done in the "after" code).
    """
    source = open("/workspace/modin/pandas/test/dataframe/test_indexing.py").read()

    # The "before" version had the helper function defined inside the for-loop.
    # Assert that this pattern is gone.
    assert (
        "for left, right in [(2, 1), (6, 1), (lambda df: 70, 1), (90, 70)]:\n\n"
        "        def _test_loc_rows(df):"
        not in source
    ), (
        "Expected `_test_loc_rows` NOT to be defined inside the `for left, right in ...` loop. "
        "The review requested moving the function definition out of the loop."
    )

    # The "after" version introduces a dedicated parametrized test for this behavior.
    assert re.search(
        r"@pytest\.mark\.parametrize\(\s*['\"]left,\s*right['\"]\s*,\s*\[\(2,\s*1\),\s*\(6,\s*1\),\s*\(lambda df:\s*70,\s*1\),\s*\(90,\s*70\)\]\s*\)\s*\n"
        r"def test_loc_insert_row\(\s*left\s*,\s*right\s*\)\s*:",
        source,
        flags=re.MULTILINE,
    ), (
        "Expected a dedicated parametrized test `test_loc_insert_row(left, right)` with "
        "`@pytest.mark.parametrize('left, right', [...])` covering the four cases from issue #3764."
    )