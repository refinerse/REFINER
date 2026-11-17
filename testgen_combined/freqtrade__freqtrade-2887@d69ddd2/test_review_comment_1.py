import inspect


def test_get_sell_rate_requires_explicit_refresh_param_no_default():
    """
    Verify `FreqtradeBot.get_sell_rate` requires an explicit `refresh` argument (no default).

    BEFORE: def get_sell_rate(self, pair: str, refresh: bool = False) -> float  (FAIL)
    AFTER:  def get_sell_rate(self, pair: str, refresh: bool) -> float          (PASS)
    """
    from freqtrade.freqtradebot import FreqtradeBot

    sig = inspect.signature(FreqtradeBot.get_sell_rate)
    refresh_param = sig.parameters.get("refresh")
    assert refresh_param is not None, "Expected 'refresh' parameter to exist on get_sell_rate()."

    assert refresh_param.default is inspect._empty, (
        "get_sell_rate(refresh=...) must not have a default. "
        "Callers must explicitly pass refresh=True/False to avoid unsafe implicit behavior."
    )