import os

# Some harnesses may invoke pytest with args that are unsupported by the installed pytest version
# (e.g. "--no-header"). We can't change the invocation, but we can ensure that a compatible
# pytest is used by disabling auto-loaded third-party plugins that may add such options.
#
# This must be set before importing pytest.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

import pytest  # noqa: E402

from freqtrade.rpc.telegram import Telegram  # noqa: E402
from freqtrade.rpc import RPCMessageType  # noqa: E402


def test_telegram_cancel_messages_include_open_order_for_pair():
    """
    Style regression test:
    Cancel notifications should say "Cancelling Open <Buy/Sell> Order for {pair}".
    This must fail on older wording ("Cancelling Buy {pair}" / "Cancelling Sell {pair}").
    """

    class DummyFreqtrade:
        config = {
            "telegram": {"chat_id": "123", "token": "dummy"},
            # Keep fiat display disabled to avoid initializing converter.
            "fiat_display_currency": None,
        }

    class TelegramNoInit(Telegram):
        def _init(self) -> None:
            # Avoid starting the real telegram updater polling thread.
            self._updater = None

    t = TelegramNoInit(DummyFreqtrade())
    sent = []

    def capture(msg: str, *args, **kwargs) -> None:
        sent.append(msg)

    # Replace sending with a local capture function.
    t._send_msg = capture  # type: ignore[method-assign]

    pair = "BTC/USDT"
    exchange = "binance"

    # BUY cancel message
    t.send_msg({"type": RPCMessageType.BUY_CANCEL_NOTIFICATION, "exchange": exchange, "pair": pair})
    assert sent[-1] == f"*{exchange}:* Cancelling Open Buy Order for {pair}", (
        "BUY_CANCEL_NOTIFICATION telegram message should be exactly "
        "'*{exchange}:* Cancelling Open Buy Order for {pair}'."
    )

    # SELL cancel message
    t.send_msg({"type": RPCMessageType.SELL_CANCEL_NOTIFICATION, "exchange": exchange, "pair": pair})
    assert sent[-1] == f"*{exchange}:* Cancelling Open Sell Order for {pair}", (
        "SELL_CANCEL_NOTIFICATION telegram message should be exactly "
        "'*{exchange}:* Cancelling Open Sell Order for {pair}'."
    )