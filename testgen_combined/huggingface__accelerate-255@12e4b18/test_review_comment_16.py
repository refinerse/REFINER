import inspect

import src.accelerate.accelerator as accelerator_mod


def test_save_state_uses_accelerator_save_not_torch_save():
    """
    Style expectation from review: internal save_state should use Accelerator.save (or higher-level helpers)
    rather than calling torch.save directly.

    This is observable by checking the source of Accelerator.save_state.
    """
    src = inspect.getsource(accelerator_mod.Accelerator.save_state)

    assert "torch.save" not in src, (
        "Accelerator.save_state should not call torch.save directly (style: use Accelerator.save or "
        "checkpointing helpers instead). Found 'torch.save' in save_state implementation."
    )