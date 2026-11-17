import pytest

from pytorch_lightning.trainer.connectors.callback_connector import CallbackConnector


class _DummyTrainer:
    def __init__(self):
        self.callbacks = []
        self.checkpoint_callbacks = []


def test_configure_progress_bar_warns_when_colab_gpu_env_is_set_to_string_zero(monkeypatch):
    """COLAB_GPU is present in Colab CPU/TPU runtimes as the string '0' (truthy).

    The warning should therefore be emitted when COLAB_GPU='0' and refresh_rate < 20.
    This fails on the "before" code because it gates on IS_COLAB instead of COLAB_GPU.
    """
    monkeypatch.setenv("COLAB_GPU", "0")

    trainer = _DummyTrainer()
    connector = CallbackConnector(trainer)

    with pytest.warns(
        UserWarning,
        match=r"You have set progress_bar_refresh_rate < 20 on Google Colab\.",
    ):
        progress_bar = connector.configure_progress_bar(refresh_rate=1, process_position=0)

    assert progress_bar is not None, "Expected a ProgressBar instance to be created when refresh_rate > 0."
    assert (
        progress_bar in trainer.callbacks
    ), "Expected the created ProgressBar callback to be appended to trainer.callbacks."