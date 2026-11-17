import re


def test_logscales_uses_parametrization_over_manual_repetition():
    """
    Ensure the reviewed test was refactored to *leverage* parametrized arguments
    for log scale inputs, instead of repeating explicit calls like:
    df.plot(logy=True), df.plot(logy='sym'), df.plot(logx=True), ...

    This is a source-level test because importing pandas test modules fails
    in this execution environment.
    """
    path = "/workspace/pandas/tests/plotting/test_frame.py"
    source = open(path, "r", encoding="utf-8").read()

    # Must have the new parametrized decorator driving logscales.
    assert (
        '@pytest.mark.parametrize("input_log, expected_log"' in source
    ), "Expected test_logscales to be parametrized over (input_log, expected_log)."

    # Must have a signature accepting those parameters.
    assert re.search(
        r"def\s+test_logscales\(\s*self\s*,\s*input_log\s*,\s*expected_log\s*\)\s*:",
        source,
    ), "Expected test_logscales(self, input_log, expected_log) signature."

    # Must use the parametrized variable in plot calls (at least one is enough).
    assert (
        "df.plot(logy=input_log)" in source
        and "df.plot(logx=input_log)" in source
        and "df.plot(loglog=input_log)" in source
    ), "Expected df.plot calls to use the parametrized 'input_log' argument."

    # The old, non-parametrized explicit calls should be gone.
    forbidden = [
        "df.plot(logy=True)",
        "df.plot(logy='sym')",
        "df.plot(logx=True)",
        "df.plot(logx='sym')",
        "df.plot(loglog=True)",
        "df.plot(loglog='sym')",
    ]
    present = [s for s in forbidden if s in source]
    assert not present, (
        "Expected manual repeated logscale plot calls to be removed in favor of "
        f"parametrization, but found: {present}"
    )