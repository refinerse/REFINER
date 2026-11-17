import re


def test_logscales_parametrized_combinations_source_inspection():
    source = open("/workspace/pandas/tests/plotting/test_frame.py", "r", encoding="utf-8").read()

    # We want to ensure the "logscales" checks were refactored into a parametrized test.
    # The "after" code has:
    #   @pytest.mark.slow
    #   @pytest.mark.parametrize("input_log, expected_log", [...])
    #   def test_logscales(self, input_log, expected_log):
    #
    # The "before" code has no parametrization decorator on test_logscales.
    pattern = re.compile(
        r"@pytest\.mark\.slow\s*\n"
        r"\s*@pytest\.mark\.parametrize\(\s*['\"]input_log,\s*expected_log['\"]\s*,",
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "Expected test_logscales to be parametrized using "
        "@pytest.mark.parametrize('input_log, expected_log', ...) immediately after "
        "@pytest.mark.slow, but that pattern was not found in "
        "/workspace/pandas/tests/plotting/test_frame.py."
    )

    # Also verify test_logscales signature includes the parametrized arguments.
    sig_pattern = re.compile(
        r"def\s+test_logscales\s*\(\s*self\s*,\s*input_log\s*,\s*expected_log\s*\)\s*:",
        re.MULTILINE,
    )
    assert sig_pattern.search(source), (
        "Expected test_logscales to accept (self, input_log, expected_log), matching the "
        "parametrization, but did not find that function signature."
    )