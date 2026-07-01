import inspect

import syft.frameworks.torch.mpc.falcon.falcon_helper as falcon_helper


def test_select_share_has_no_debug_prints_in_source():
    """
    Structural check: ensure debug prints were removed from FalconHelper.select_share.

    This is a review-requested structural cleanup with no required functional output changes,
    so we verify by inspecting the function source directly.
    """
    src = inspect.getsource(falcon_helper.FalconHelper.select_share)

    assert "print(" not in src, (
        "FalconHelper.select_share should not contain debug print statements. "
        "Remove any `print(...)` calls to avoid noisy stdout during MPC operations."
    )