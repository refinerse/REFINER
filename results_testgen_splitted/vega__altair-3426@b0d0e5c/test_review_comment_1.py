import altair.utils.data as aud


def test_curry_removed_from_altair_utils_data_public_api():
    """
    Style requirement: altair.utils.data.curry is marked for removal and should
    no longer be part of the module's public/runtime API surface.
    """
    assert not hasattr(
        aud, "curry"
    ), "altair.utils.data.curry is marked for removal; it should not exist on the module."