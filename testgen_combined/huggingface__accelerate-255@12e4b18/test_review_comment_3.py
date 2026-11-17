import inspect

import src.accelerate.accelerator as accelerator_mod


def test_accelerator_save_state_uses_checkpointing_helpers():
    """
    Style/API expectation from review: Accelerator.save_state should delegate to
    save_accelerator_state (rather than manually constructing file paths and calling torch.save).
    This is observable via presence of the checkpointing helper name in the method source.
    """
    src = inspect.getsource(accelerator_mod.Accelerator.save_state)

    assert (
        "save_accelerator_state" in src
    ), "Expected Accelerator.save_state to delegate to checkpointing.save_accelerator_state()."

    assert (
        "torch.save" not in src
    ), "Expected Accelerator.save_state to avoid direct torch.save calls (should be handled in checkpointing helper)."

    # Ensure the module import wiring exists too (guards against local name references without proper import).
    module_src = open("/workspace/src/accelerate/accelerator.py", "r", encoding="utf-8").read()
    assert (
        "from .checkpointing import load_accelerator_state, save_accelerator_state" in module_src
    ), "Expected accelerator.py to import checkpointing helpers for save_state/load_state delegation."