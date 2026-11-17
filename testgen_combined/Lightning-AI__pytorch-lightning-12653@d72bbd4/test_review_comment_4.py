import re

import tests.trainer.connectors.test_data_connector as tdc


def test_parametrize_argument_names_use_warns_not_raises_exception():
    """The review change renames the parametrize argument from `raises_exception` to `warns`.

    This is not a runtime behavior change of the library, but it *is* a functional change for the test module:
    the argument name must match the function signature used in the parametrized test.
    """
    # Ensure the test function exists and has the updated parameter name
    fn = tdc.test_non_sequential_sampler_warning_is_raised_for_eval_dataloader
    varnames = fn.__code__.co_varnames[: fn.__code__.co_argcount]
    assert varnames == ("val_dl", "warns"), (
        "Expected parametrized test function to accept arguments ('val_dl', 'warns'). "
        f"Got {varnames}. This indicates the review suggestion was not applied."
    )

    # Ensure the decorator uses the updated argument names string (source-level check, stable and explicit)
    source = open("/workspace/tests/trainer/connectors/test_data_connector.py", "r", encoding="utf-8").read()

    assert '"val_dl,warns"' in source, (
        'Expected the parametrize decorator to declare argument names as "val_dl,warns" '
        "(matching the function signature)."
    )
    assert '"val_dl,raises_exception"' not in source, (
        'Did not expect the old parametrize argument names "val_dl,raises_exception" to remain in the file.'
    )

    # Sanity: the function definition should also use the updated name
    assert re.search(
        r"def\s+test_non_sequential_sampler_warning_is_raised_for_eval_dataloader\s*\(\s*val_dl\s*,\s*warns\s*\)\s*:",
        source,
    ), "Expected function signature to be `(..., warns)` in the source."