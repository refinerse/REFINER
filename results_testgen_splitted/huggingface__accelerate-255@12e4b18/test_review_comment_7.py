import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_model_weight_filenames_are_unindexed_for_first_model():
    """
    Regression test for checkpoint naming: when saving multiple models, the first model
    should be saved as 'pytorch_model.bin' (no _0 suffix). Subsequent models should use
    'pytorch_model_1.bin', etc.

    This fails on the "before" code because it incorrectly adds '_0' for i == 0.
    """
    acc = Accelerator(cpu=True)

    # Avoid depending on accelerator.prepare() side effects: directly register models.
    acc._models = [torch.nn.Linear(2, 2), torch.nn.Linear(2, 2)]
    acc._optimizers = []  # keep empty to avoid optimizer file naming differences

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)

        expected_first = os.path.join(tmpdir, "pytorch_model.bin")
        unexpected_first = os.path.join(tmpdir, "pytorch_model_0.bin")
        expected_second = os.path.join(tmpdir, "pytorch_model_1.bin")

        assert os.path.isfile(
            expected_first
        ), f"Expected first model checkpoint to be saved as '{expected_first}' (no '_0' suffix)."
        assert not os.path.isfile(
            unexpected_first
        ), f"Did not expect a '_0' suffixed checkpoint for the first model: '{unexpected_first}'."
        assert os.path.isfile(
            expected_second
        ), f"Expected second model checkpoint to be saved as '{expected_second}' (with '_1' suffix)."