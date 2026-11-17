import re


def test_issue_3764_loc_tests_split_and_parametrized():
    """
    Verify that the issue #3764 regression test was moved out of `test_loc`
    into its own test cases and uses `@pytest.mark.parametrize("left, right", ...)`.

    This is a structural/functional test of the test suite organization change requested
    in the code review comment.
    """
    source = open("/workspace/modin/pandas/test/dataframe/test_indexing.py").read()

    # After-version expectation: new parametrized test function exists.
    assert (
        '@pytest.mark.parametrize("left, right", [(2, 1), (6, 1), (lambda df: 70, 1), (90, 70)])'
        in source
    ), (
        "Expected issue #3764 row-insertion test to be split into a separate test case "
        "and parametrized with @pytest.mark.parametrize('left, right', ...)."
    )

    assert "def test_loc_insert_row(left, right):" in source, (
        "Expected a dedicated `test_loc_insert_row(left, right)` test function for issue #3764, "
        "instead of embedding the loop inside `test_loc`."
    )

    # Before-version had the loop inside `test_loc`: `for left, right in [...]`
    assert (
        "for left, right in [(2, 1), (6, 1), (lambda df: 70, 1), (90, 70)]" not in source
    ), (
        "Did not expect a hard-coded `for left, right in [...]` loop in the file; "
        "it should be replaced by pytest parametrization in a separate test."
    )

    # Ensure the new column insertion test is also split out as a separate test function.
    # (Not strictly required by the review comment, but it was part of the refactor in the diff.)
    assert "def test_loc_insert_col(columns):" in source, (
        "Expected issue #3764 column-insertion test to be split into a separate "
        "`test_loc_insert_col(columns)` test function."
    )

    # Ensure issue #3764 block is no longer present inside `test_loc`.
    # This checks that within the body of `test_loc` there is no "From issue #3764" comment.
    m = re.search(r"def test_loc\([^)]*\):(.+?)\n\n", source, flags=re.S)
    assert m is not None, "Could not locate the `test_loc` function body to verify it was cleaned up."
    test_loc_body = m.group(1)
    assert "From issue #3764" not in test_loc_body, (
        "Expected the issue #3764 regression tests to be moved out of `test_loc` "
        "into separate test cases."
    )