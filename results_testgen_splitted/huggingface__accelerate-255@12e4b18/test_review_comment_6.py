import os
import tempfile

import torch

from src.accelerate import Accelerator


def test_save_state_saves_rng_state_per_process_with_trainer_style_name():
    """
    The reviewed change requires:
      - using Trainer-consistent name: `rng_state.pth`
      - saving RNG state per process: `rng_state_{i}.pth`

    The "before" implementation saved a single `random_states.pkl` file, so it should fail this test.
    """
    acc = Accelerator(cpu=True)

    model = torch.nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    acc.prepare(model, optimizer)

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)

        expected_rng_file = os.path.join(tmpdir, f"rng_state_{acc.state.process_index}.pth")
        assert os.path.isfile(expected_rng_file), (
            "Accelerator.save_state() should save per-process RNG state using Trainer-consistent naming "
            f"`rng_state_<process_index>.pth`. Expected to find {expected_rng_file}, but it was not created."
        )

        legacy_rng_file = os.path.join(tmpdir, "random_states.pkl")
        assert not os.path.exists(legacy_rng_file), (
            "Accelerator.save_state() should not save RNG state under the legacy name `random_states.pkl`. "
            "Found that file, indicating the old checkpoint format is still being used."
        )