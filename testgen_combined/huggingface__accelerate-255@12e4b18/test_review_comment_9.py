import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_uses_checkpointing_constants_single_model_naming():
    """
    Regression test for review comment: "The names should probably be constants".

    Observable behavior: after the change, Accelerator.save_state delegates to
    accelerate.checkpointing.save_accelerator_state which uses consistent filenames,
    including `pytorch_model.bin` for a single model.

    Before the change, save_state hardcoded strings and produced `pytorch_model_0.bin`
    (note the `_0`) even for a single model.
    """
    acc = Accelerator(cpu=True)
    model = torch.nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    acc.prepare(model, optimizer)

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)
        files = set(os.listdir(tmpdir))

        assert (
            "pytorch_model.bin" in files
        ), f"Expected `save_state()` to create `pytorch_model.bin` for a single model (consistent constant-based naming). Got files: {sorted(files)}"