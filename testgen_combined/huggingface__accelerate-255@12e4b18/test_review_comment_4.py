import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_uses_checkpointing_module_naming_instead_of_optimizer_index_files():
    """
    The "before" implementation manually torch.saves model/optimizer/scaler/random states and (notably) always names
    optimizer-like objects as `optimizer_0.pt`, `optimizer_1.pt`, ... even if one of them is actually a LR scheduler.

    The "after" implementation delegates to `accelerate.checkpointing.save_accelerator_state`, which uses canonical
    filenames (e.g. `pytorch_model.bin`, `optimizer.pt`, etc.) instead of the old indexed optimizer filenames.

    This test asserts that `optimizer_0.pt` is NOT created anymore when saving state with one optimizer.
    - FAILS on "before" (it creates optimizer_0.pt)
    - PASSES on "after" (it should not create optimizer_0.pt)
    """
    accelerator = Accelerator(cpu=True)

    model = torch.nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    # Populate internal lists as save_state() relies on these.
    accelerator._models = [model]
    accelerator._optimizers = [optimizer]

    with tempfile.TemporaryDirectory() as tmpdir:
        accelerator.save_state(tmpdir)

        legacy_file = os.path.join(tmpdir, "optimizer_0.pt")
        assert not os.path.exists(legacy_file), (
            "save_state() should use the new checkpointing implementation (accelerate.checkpointing.save_accelerator_state) "
            "and therefore must not create legacy indexed optimizer files like 'optimizer_0.pt'."
        )