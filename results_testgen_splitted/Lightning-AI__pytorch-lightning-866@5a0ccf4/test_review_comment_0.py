import warnings

import pytest

from pytorch_lightning.trainer.training_io import TrainerIOMixin


class _DummyTrainer(TrainerIOMixin):
    """Concrete class to test TrainerIOMixin.restore_training_state in isolation."""

    def __init__(self):
        super().__init__()
        self.checkpoint_callback = None
        self.early_stop_callback = None
        self.root_gpu = None  # avoid optimizer state CUDA move path
        self.optimizers = []
        self.lr_schedulers = []


def test_restore_training_state_mid_epoch_warning_respects_grad_accumulation():
    """
    Regression test for mid-epoch resume warning logic.

    When accumulate_grad_batches > 1, global_step advances once per accumulated batch.
    Resuming at global_step==expected_steps (end of epoch) should NOT warn.

    Before fix: used abs((global_step + 1) % num_training_batches) which warns incorrectly.
    After fix: uses expected_steps = num_training_batches / accumulate_grad_batches.
    """
    t = _DummyTrainer()
    t.num_training_batches = 10
    # attribute exists only in "after"; set defensively so this test runs on both versions
    t.accumulate_grad_batches = 2

    checkpoint = {
        "global_step": 5,  # end-of-epoch when expected_steps = 10/2 = 5
        "epoch": 0,
        "optimizer_states": [],
        "lr_schedulers": [],
    }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t.restore_training_state(checkpoint)

    assert not any("ended mid-epoch" in str(w.message) for w in caught), (
        "restore_training_state should not warn about resuming mid-epoch when global_step "
        "corresponds to an epoch boundary after accounting for accumulate_grad_batches. "
        f"Got warnings: {[str(w.message) for w in caught]}"
    )