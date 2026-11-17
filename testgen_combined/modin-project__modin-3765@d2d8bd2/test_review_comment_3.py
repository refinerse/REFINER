import re


def test_issue_3764_loc_tests_are_split_out_of_test_loc_and_parametrized():
    source = open("/workspace/modin/pandas/test/dataframe/test_indexing.py").read()

    # The review comment asked to move function definitions out of the loop.
    # The accepted fix was to split the loop-driven checks from `test_loc`
    # into standalone parametrized tests `test_loc_insert_row` and `test_loc_insert_col`.
    assert "def test_loc_insert_row" in source, (
        "Expected standalone `test_loc_insert_row` to exist (issue #3764 checks moved out "
        "of the loop in `test_loc`)."
    )
    assert "def test_loc_insert_col" in source, (
        "Expected standalone `test_loc_insert_col` to exist (issue #3764 checks moved out "
        "of the loop in `test_loc`)."
    )

    # Ensure `test_loc` no longer contains the issue #3764 loops.
    m = re.search(r"^def test_loc\(.*?\):(?P<body>.*?)(?=^\s*def |\Z)", source, flags=re.S | re.M)
    assert m, "Could not locate `test_loc` function definition in source file."
    test_loc_body = m.group("body")

    assert "From issue #3764" not in test_loc_body, (
        "`test_loc` should no longer include the inline issue #3764 block; "
        "it should be moved into separate parametrized tests."
    )
    assert "for left, right in" not in test_loc_body, (
        "`test_loc` should not contain the loop over `(left, right)` pairs for issue #3764; "
        "these cases should be covered by `test_loc_insert_row` parametrization."
    )
    assert "for columns in" not in test_loc_body, (
        "`test_loc` should not contain the loop over `columns` for issue #3764; "
        "these cases should be covered by `test_loc_insert_col` parametrization."
    )