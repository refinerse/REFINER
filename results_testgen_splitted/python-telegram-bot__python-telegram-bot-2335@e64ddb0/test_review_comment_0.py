import inspect

import examples.deeplinking as deeplinking


def test_deeplinking_uses_bot_username_property_not_get_me_username():
    """
    Style requirement from review: use Bot.username convenience property instead of
    bot.get_me().username when building deep-link URLs.

    This test inspects the source of the module functions to ensure `.get_me().username`
    is not used in URL creation anymore.
    """
    functions_to_check = [
        deeplinking.start,
        deeplinking.deep_linked_level_1,
        deeplinking.deep_linked_level_2,
        deeplinking.deep_link_level_3_callback,
    ]

    offending = []
    for func in functions_to_check:
        src = inspect.getsource(func)
        if "get_me().username" in src:
            offending.append(func.__name__)

    assert not offending, (
        "Deep-linking example should use `bot.username` (Bot convenience property) instead of "
        "`bot.get_me().username`. Offending functions: "
        f"{', '.join(offending)}"
    )