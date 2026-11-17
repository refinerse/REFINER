import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_uses_trainer_scaler_filename_scaler_pt():
    """
    Style requirement: the GradScaler checkpoint filename should match Trainer's convention: 'scaler.pt'.

    This is not directly exposed via a constant, so we functionally observe the filename produced by calling
    Accelerator.save_state() with a scaler present, and checking the files written to disk.
    """
    acc = Accelerator(mixed_precision="fp16")  # ensures acc.scaler is not None (on CPU too)

    # Add a trivial model + optimizer to ensure save_state does full checkpointing, like real usage.
    model = torch.nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    acc.prepare(model, optimizer)

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)

        expected = os.path.join(tmpdir, "scaler.pt")
        assert os.path.isfile(expected), (
            "Accelerator.save_state() should save the GradScaler state using the Trainer-compatible filename "
            "'scaler.pt'. If this file is missing, the code likely used a different filename such as 'scaler.bin'."
        )