import tempfile

import torch

from src.accelerate.accelerator import Accelerator
from src.accelerate.utils import save as accelerate_utils_save


def test_save_state_uses_accelerate_utils_save_indirection_not_torch_save_direct_call():
    """
    Review requirement: save_state should use accelerator/accelerate saving utilities (not call torch.save directly),
    otherwise it won't work for TPUs.

    Observable behavior difference:
    - BEFORE: Accelerator.save_state calls torch.save(...) directly.
    - AFTER: Accelerator.save_state delegates to checkpointing which calls accelerate.utils.save(...), which then
      calls torch.save(...).

    We assert that `torch.save` is only called *from* `accelerate.utils.save` (the indirection layer),
    and never directly from `Accelerator.save_state` (or other non-accelerate code paths).
    """
    accelerator = Accelerator(cpu=True)
    model = torch.nn.Linear(2, 2)
    accelerator.prepare(model)

    orig_torch_save = torch.save

    def guarded_torch_save(*args, **kwargs):
        # torch.save should only be invoked via accelerate.utils.save (TPU-safe indirection layer)
        caller = guarded_torch_save.__wrapped__  # set below

        if caller is not accelerate_utils_save:
            raise AssertionError(
                "Accelerator.save_state must not call torch.save directly. "
                "torch.save should be reached only via accelerate.utils.save (TPU-safe path)."
            )
        return orig_torch_save(*args, **kwargs)

    # Minimal, no-mock way to know the direct caller: set a function attribute just before calling torch.save
    # inside accelerate_utils_save by wrapping accelerate_utils_save itself.
    orig_accelerate_utils_save = accelerate_utils_save

    def wrapped_accelerate_utils_save(obj, f):
        guarded_torch_save.__wrapped__ = wrapped_accelerate_utils_save
        return orig_accelerate_utils_save(obj, f)

    # Initialize attribute to something not equal to accelerate_utils_save
    guarded_torch_save.__wrapped__ = None

    # Patch both torch.save and accelerate.utils.save at runtime.
    torch.save = guarded_torch_save
    import src.accelerate.utils as utils_mod

    utils_mod.save = wrapped_accelerate_utils_save
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            accelerator.save_state(tmpdir)
    finally:
        torch.save = orig_torch_save
        utils_mod.save = orig_accelerate_utils_save