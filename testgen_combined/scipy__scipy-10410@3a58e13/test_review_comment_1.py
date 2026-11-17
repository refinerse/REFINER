import re


def test_ncx2_zero_nc_tests_use_tight_tolerance_and_small_x():
    """
    The reviewed change tightened tolerances (atol=1e-15, no rtol) and changed
    the evaluation point from x=1 to x=0.1 in the ncx2 zero-nonc test.

    This test inspects the repository test source to ensure those exact choices
    are present, because they are the behavioral change requested in the review.
    """
    path = "/workspace/scipy/stats/tests/test_distributions.py"
    source = open(path, "r", encoding="utf-8").read()

    # Ensure the test is using x=0.1 (after) rather than x=1 (before).
    # Look specifically for the ncx2_zero_nc test body and its call.
    assert "def test_ncx2_zero_nc(method, expected):" in source, (
        "Expected test_ncx2_zero_nc to exist in scipy/stats/tests/test_distributions.py"
    )

    # Must call ncx2 method with x=0.1
    assert re.search(
        r"getattr\(stats\.ncx2,\s*method\)\(\s*0\.1\s*,\s*nc=\[0,\s*4\]\s*,\s*df=10\s*\)",
        source,
        flags=re.MULTILINE,
    ), (
        "Expected test_ncx2_zero_nc to evaluate at x=0.1 with nc=[0, 4], df=10 "
        "(this was changed from x=1 in the pre-review version)."
    )

    # Must use assert_allclose with atol=1e-15 and *no* rtol.
    m = re.search(
        r"assert_allclose\(\s*result\s*,\s*expected\s*,\s*([^)]+)\)",
        source,
        flags=re.MULTILINE,
    )
    assert m, "Expected an assert_allclose(result, expected, ...) call in test_ncx2_zero_nc."
    assert "atol=1e-15" in m.group(1), (
        "Expected test_ncx2_zero_nc to use atol=1e-15 (tight tolerance per review)."
    )
    assert "rtol" not in m.group(1), (
        "Expected test_ncx2_zero_nc to avoid specifying rtol (old code used rtol=1e-3)."
    )

    # For the rvs test, ensure it uses scalar nc=0 and compares to chi2.rvs
    # with tight atol=1e-15 (after) rather than vectorized nc=[0,4] + hardcoded expected (before).
    assert "def test_ncx2_zero_nc_rvs():" in source, (
        "Expected test_ncx2_zero_nc_rvs to exist in scipy/stats/tests/test_distributions.py"
    )
    assert "stats.ncx2.rvs(df=10, nc=0, random_state=1)" in source, (
        "Expected test_ncx2_zero_nc_rvs to draw with nc=0 (scalar) and random_state=1."
    )
    assert "expected = stats.chi2.rvs(df=10, random_state=1)" in source, (
        "Expected test_ncx2_zero_nc_rvs to compare against stats.chi2.rvs with the same seed."
    )
    assert "assert_allclose(result, expected, atol=1e-15)" in source, (
        "Expected test_ncx2_zero_nc_rvs to use tight atol=1e-15 in assert_allclose."
    )