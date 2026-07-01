import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_does_not_suffix_first_optimizer_with_0():
    """
    The behavioral change requested in the review comment is that index 0 should NOT get a "_0" suffix.
    Concretely, after saving state for a single optimizer, there should be no "optimizer_0.pt" file.

    This fails on the before code (it creates optimizer_0.pt) and passes on the after code
    (which delegates to checkpointing utilities and does not create optimizer_0.pt).
    """
    acc = Accelerator(cpu=True)

    model = torch.nn.Linear(2, 2)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)

    # Ensure Accelerator tracks exactly one optimizer.
    acc.prepare(model, opt)
    assert len(acc._optimizers) == 1, "Test setup expects exactly one prepared optimizer in Accelerator."

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)

        wrong = os.path.join(tmpdir, "optimizer_0.pt")
        assert not os.path.exists(wrong), (
            "save_state() should not create 'optimizer_0.pt' for the first optimizer (index 0). "
            "Index 0 should not be suffixed."
        )