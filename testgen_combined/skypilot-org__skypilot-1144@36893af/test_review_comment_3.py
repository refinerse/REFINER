import importlib

import sky.backends.wheel_utils as wheel_utils


def test_private_helper_renamed_to_get_latest_wheel_and_remove_all_others():
    """Style: ensure helper function name matches review comment rename.

    Before: _get_latest_wheel_and_cleanup
    After:  _get_latest_wheel_and_remove_all_others
    """
    # Reload to avoid any potential cross-test pollution.
    mod = importlib.reload(wheel_utils)

    assert hasattr(
        mod, "_get_latest_wheel_and_remove_all_others"
    ), (
        "Expected wheel_utils to define the helper function "
        "`_get_latest_wheel_and_remove_all_others()` (as per review comment), "
        "but it was not found."
    )
    assert not hasattr(
        mod, "_get_latest_wheel_and_cleanup"
    ), (
        "Did not expect wheel_utils to still define the old helper function "
        "`_get_latest_wheel_and_cleanup()` after the style rename."
    )