import re


def test_moment_precision_loss_heuristic_and_message_updated():
    source = open("/workspace/scipy/stats/_stats_py.py", "r", encoding="utf-8").read()

    # The fix reduces the tolerance multiplier from 1e6 to 10.
    assert "np.finfo(a_zero_mean.dtype).resolution * 10" in source, (
        "Expected _moment precision-loss check to use a much smaller tolerance "
        "(resolution * 10). This ensures warnings only occur on nearly-identical "
        "data, not on valid inputs."
    )

    # The fix uses abs(mean) in the denominator to avoid sign issues.
    # Accept either the line-broken or single-line formatting.
    assert ("/ np.abs(mean)" in source) or ("/np.abs(mean)" in source), (
        "Expected _moment relative difference to divide by np.abs(mean) "
        "to avoid incorrect behavior when mean is negative."
    )

    # The fix simplifies the precision-loss condition to `rel_diff < eps`
    # (and no longer requires `0 < rel_diff`).
    assert re.search(r"precision_loss\s*=\s*np\.any\(\s*rel_diff\s*<\s*eps\s*\)", source), (
        "Expected _moment precision-loss condition to be `np.any(rel_diff < eps)` "
        "(no extra `0 < rel_diff` guard)."
    )

    # The warning message should mention "catastrophic" (spelling fixed)
    # and explain that this occurs when data are nearly identical.
    assert "catastrophic cancellation" in source, (
        "Expected precision-loss warning message to contain the correctly spelled "
        "'catastrophic cancellation'."
    )
    assert "nearly identical" in source, (
        "Expected precision-loss warning message to explain it occurs when the data "
        "are nearly identical."
    )