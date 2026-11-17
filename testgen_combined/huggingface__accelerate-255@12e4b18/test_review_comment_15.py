import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_does_not_create_index0_suffix_files():
    """
    Style requirement: filenames should not include an unnecessary '_0' suffix for the first model/optimizer.
    Before code incorrectly used `if i == 0: name += f"_{i}"`, creating 'pytorch_model_0.bin' and 'optimizer_0.pt'.
    After code delegates to checkpointing utils that use the conventional no-suffix naming for index 0.
    """
    acc = Accelerator(cpu=True)

    # Register one model + optimizer with the Accelerator internals.
    model = torch.nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    acc.prepare(model, optimizer)

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)
        saved = set(os.listdir(tmpdir))

        assert (
            "pytorch_model_0.bin" not in saved
        ), "save_state() should not create 'pytorch_model_0.bin' (unnecessary index-0 suffix)."
        assert (
            "optimizer_0.pt" not in saved
        ), "save_state() should not create 'optimizer_0.pt' (unnecessary index-0 suffix)."