import inspect

import pandas.tools.tile as tile


def test_bins_to_cuts_signature_no_longer_has_retbins_or_name():
    """
    The review comment states `retbins` and `name` are no longer used in
    `_bins_to_cuts`. Verify the function signature reflects that by not
    accepting these parameters.

    This fails on the "before" code where `_bins_to_cuts` still declares
    `retbins` and `name`, and passes on the "after" code where they are removed.
    """
    sig = inspect.signature(tile._bins_to_cuts)
    params = sig.parameters

    assert "retbins" not in params, (
        "`_bins_to_cuts` should not accept a `retbins` parameter anymore; "
        "it is handled by postprocessing in `cut/qcut`."
    )
    assert "name" not in params, (
        "`_bins_to_cuts` should not accept a `name` parameter anymore; "
        "name propagation is handled by `_preprocess_for_cut/_postprocess_for_cut`."
    )