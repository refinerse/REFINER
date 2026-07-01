import os
import pytest

from pytorch_lightning.trainer.connectors.callback_connector import CallbackConnector


class _DummyTrainer:
    def __init__(self):
        self.callbacks = []
        self.checkpoint_callbacks = []


def test_configure_progress_bar_warns_on_colab_env_var():
    """The Colab crash warning should trigger when the COLAB_GPU env var is set and refresh_rate < 20.

    - BEFORE: uses a static `IS_COLAB` flag, so setting COLAB_GPU at runtime may not trigger a warning.
    - AFTER: uses `os.getenv("COLAB_GPU")`, so setting COLAB_GPU should always trigger the warning.
    """
    trainer = _DummyTrainer()
    connector = CallbackConnector(trainer)

    os.environ["COLAB_GPU"] = "1"
    try:
        with pytest.warns(UserWarning, match=r"COLAB|Google Colab|progress_bar_refresh_rate"):
            connector.configure_progress_bar(refresh_rate=1, process_position=0)
    finally:
        os.environ.pop("COLAB_GPU", None)