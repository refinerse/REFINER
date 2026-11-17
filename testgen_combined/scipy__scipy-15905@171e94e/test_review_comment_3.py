import re


def test__moment_precision_loss_detects_exact_constant_inputs_and_warning_message_spelling():
    source = open("/workspace/scipy/stats/_stats_py.py", "r", encoding="utf-8").read()

    # The review comment requests that the "precision loss" warning should
    # trigger even when all the data are exactly equal, i.e. rel_diff == 0.
    # That requires `precision_loss = np.any(rel_diff < eps)` rather than
    # requiring `0 < rel_diff`.
    assert "precision_loss = np.any(rel_diff < eps)" in source, (
        "Regression test for constant-input precision-loss detection: expected "
        "`precision_loss = np.any(rel_diff < eps)` so that the warning triggers "
        "even when rel_diff == 0 (exactly constant/identical data)."
    )
    assert "precision_loss = np.any((0 < rel_diff) & (rel_diff < eps))" not in source, (
        "The old logic required `0 < rel_diff`, which suppresses the precision-loss "
        "warning when inputs are exactly constant; this should be removed."
    )

    # Also ensure the warning message was corrected (spelling + more informative text).
    assert "catastrophic cancellation" in source, (
        "Expected warning message to mention 'catastrophic cancellation' (spelling fixed)."
    )
    assert "catastrophc cancellation" not in source, (
        "Old warning message contained typo 'catastrophc cancellation'; should be fixed."
    )
    assert "nearly identical" in source, (
        "Expected warning message to explain that catastrophic cancellation occurs "
        "when the data are nearly identical."
    )

    # Sanity check: ensure we're checking the warning inside `_moment`.
    assert re.search(r"def _moment\([\s\S]*?precision_loss", source), (
        "Test expects `_moment` to contain precision-loss detection logic."
    )