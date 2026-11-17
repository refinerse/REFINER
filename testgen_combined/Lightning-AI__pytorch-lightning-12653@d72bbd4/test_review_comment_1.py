import re

import pytest

import tests.trainer.connectors.test_data_connector as tdc


def test_non_sequential_sampler_param_name_is_warns_not_raises_exception():
    """The reviewed change renames the parametrized boolean from `raises_exception` to `warns`.

    This is not a runtime behavior change in Lightning itself, but a correctness/clarity change in the test.
    We assert that the test function signature uses the new parameter name, ensuring the review suggestion
    got applied.
    """
    # The function is defined in the imported module (no fragile path logic needed)
    assert hasattr(
        tdc, "test_non_sequential_sampler_warning_is_raised_for_eval_dataloader"
    ), "Expected the test function to exist in tests.trainer.connectors.test_data_connector"

    func = tdc.test_non_sequential_sampler_warning_is_raised_for_eval_dataloader
    varnames = func.__code__.co_varnames[: func.__code__.co_argcount]

    assert "warns" in varnames, (
        "Expected the test function to take a boolean parameter named `warns` "
        "(as per review suggestion), but it was not found. "
        f"Found parameters: {varnames}"
    )
    assert "raises_exception" not in varnames, (
        "The old parameter name `raises_exception` should have been renamed to `warns` "
        "as per the review comment, but it is still present. "
        f"Found parameters: {varnames}"
    )

    # Extra guard to ensure we are really checking the target test, not another function.
    src = open("/workspace/tests/trainer/connectors/test_data_connector.py", "r", encoding="utf-8").read()
    assert re.search(
        r"def test_non_sequential_sampler_warning_is_raised_for_eval_dataloader\(val_dl,\s*warns\)\s*:",
        src,
    ), "Expected source to define the test with signature (val_dl, warns)"