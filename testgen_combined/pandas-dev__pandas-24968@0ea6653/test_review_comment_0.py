import re


def test_logscales_parametrized_and_invalid_logscale_uses_dict_expansion():
    source = open("/workspace/pandas/tests/plotting/test_frame.py", encoding="utf-8").read()

    # The review-intended change consolidates repeated log-scale checks into
    # a single parametrized test over (input_log, expected_log).
    assert 'def test_logscales(self, input_log, expected_log):' in source, (
        "Expected test_logscales to be refactored to accept (input_log, expected_log) "
        "parameters (parametrized), but did not find the new function signature."
    )

    assert '@pytest.mark.parametrize("input_log, expected_log"' in source, (
        "Expected test_logscales to be parametrized over (input_log, expected_log), "
        "but did not find the parametrize decorator."
    )

    # And the invalid logscale test must pass invalid values to one of logx/logy/loglog
    # via dict expansion, not via a non-existent keyword like input_param=...
    assert "df.plot(**{input_param: \"sm\"})" in source, (
        "Expected invalid logscale test to call df.plot with a dynamically-selected "
        "parameter via dict expansion: df.plot(**{input_param: 'sm'})."
    )

    # Ensure the incorrect suggested call isn't present.
    assert "df.plot(input_param=input_param" not in source, (
        "Found df.plot(input_param=input_param...) in the test file, but plot() does not "
        "take an 'input_param' keyword; the test should pass logx/logy/loglog dynamically."
    )

    # Additionally ensure we are not still hardcoding separate calls for both True and 'sym'
    # in the same test body (a sign the refactor didn't happen). This is a light heuristic.
    # In the refactored version, logy/logx/loglog should each be called exactly once with input_log.
    for key in ["logy=", "logx=", "loglog="]:
        assert source.count(f"df.plot({key}input_log)") == 1, (
            f"Expected exactly one call using input_log for {key[:-1]}, "
            f"but found {source.count(f'df.plot({key}input_log)')}."
        )

    # Verify expected_log is used in assertions for scale.
    assert re.search(r"assert ax\.get_yscale\(\) == expected_log", source), (
        "Expected assertion 'ax.get_yscale() == expected_log' in parametrized logscale test."
    )
    assert re.search(r"assert ax\.get_xscale\(\) == expected_log", source), (
        "Expected assertion 'ax.get_xscale() == expected_log' in parametrized logscale test."
    )