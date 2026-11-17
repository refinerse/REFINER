import re


def test_no_pytest_filterwarnings_error_and_uses_catch_warnings_error_filter():
    """
    Regression test for review comment: the test file should not use
    `@pytest.mark.filterwarnings("error")` to assert no warnings are emitted.
    Instead, it should use the Pytest-recommended pattern:

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ...

    This test is source-based because importing sklearn.compose.tests.test_target
    fails in this execution environment.
    """
    path = "/workspace/sklearn/compose/tests/test_target.py"
    source = open(path, encoding="utf-8").read()

    assert (
        '@pytest.mark.filterwarnings("error")' not in source
    ), (
        "Expected sklearn/compose/tests/test_target.py to stop using "
        '@pytest.mark.filterwarnings("error") and instead rely on '
        "warnings.catch_warnings() + warnings.simplefilter('error')."
    )

    # Check for the recommended warnings pattern (allow whitespace/newlines variations).
    catch_pat = re.compile(r"with\s+warnings\.catch_warnings\(\)\s*:", re.MULTILINE)
    simplefilter_pat = re.compile(
        r"warnings\.simplefilter\(\s*(['\"])error\1\s*\)", re.MULTILINE
    )

    assert catch_pat.search(source), (
        "Expected sklearn/compose/tests/test_target.py to use "
        "`with warnings.catch_warnings():` to make warnings raise during the "
        "relevant fit call."
    )
    assert simplefilter_pat.search(source), (
        "Expected sklearn/compose/tests/test_target.py to call "
        "`warnings.simplefilter('error')` inside a catch_warnings context."
    )