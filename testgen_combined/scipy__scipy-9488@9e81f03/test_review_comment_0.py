import re


def test_gmean_hmean_tests_use_rtol_helpers_and_no_significant_to_rtol_conversion():
    """
    This change replaced a `significant` argument (converted to rtol via
    np.float_power) with explicit `rtol` in the gmean/hmean helper functions.

    We verify, via source inspection, that:
    - new helpers `check_equal_gmean` and `check_equal_hmean` exist and take rtol
    - the old `StatsTestMethod.equal_test(... significant=...)` helper is gone
    - the specific conversion pattern `rtol = np.float_power(10, -1.0 * significant)`
      is absent (roundabout tolerance computation removed)

    Note: the file still legitimately uses `significant=` elsewhere (e.g. in
    assert_approx_equal calls); we must not forbid that globally.
    """
    path = "/workspace/scipy/stats/tests/test_stats.py"
    source = open(path, "r", encoding="utf-8").read()

    assert re.search(r"^def\s+check_equal_gmean\([^)]*\brtol\s*=\s*1e-7", source, re.M), (
        "Expected helper `check_equal_gmean(..., rtol=1e-7)` to exist in "
        f"{path}, indicating the tests accept explicit rtol."
    )
    assert re.search(r"^def\s+check_equal_hmean\([^)]*\brtol\s*=\s*1e-7", source, re.M), (
        "Expected helper `check_equal_hmean(..., rtol=1e-7)` to exist in "
        f"{path}, indicating the tests accept explicit rtol."
    )

    assert "class StatsTestMethod" not in source, (
        "Legacy helper `class StatsTestMethod` (with `significant` argument) "
        "should have been removed in favor of rtol-based helper functions."
    )

    assert "rtol = np.float_power(10, -1.0 * significant)" not in source, (
        "Did not expect roundabout conversion from `significant` to `rtol` via "
        "`np.float_power(10, -1.0 * significant)`; tests should specify `rtol` "
        "directly."
    )