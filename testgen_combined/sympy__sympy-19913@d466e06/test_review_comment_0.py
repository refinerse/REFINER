def test_review_comment_updates_expected_string_literal_for_loggamma_mapping():
    source = open("/workspace/sympy/printing/tests/test_pycode.py", "r", encoding="utf-8").read()

    assert "assert p.doprint(loggamma(x))" in source, (
        "Expected the test file under review to contain an assertion about how "
        "MpmathPrinter prints loggamma(x)."
    )

    assert "assert p.doprint(loggamma(x)) == 'mpmath.loggamma(x)'" in source, (
        "Regression test for the review comment: the repository test should assert that "
        "MpmathPrinter prints loggamma(x) as 'mpmath.loggamma(x)'. "
        "This should fail if the file still expects 'mpmath.lgamma(x)'."
    )