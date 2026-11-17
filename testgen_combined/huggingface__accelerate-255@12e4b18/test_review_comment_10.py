import os
import tempfile

import torch
from src.accelerate.accelerator import Accelerator


def test_save_state_writes_process_index_specific_random_states_file():
    """
    Review expectation: "one for each process" -> at least some checkpoint artifacts must be
    process-index specific to avoid collisions.

    The merged ("after") implementation writes RNG state as `random_states_{process_index}.pkl`.
    The pre-merge ("before") implementation always writes `random_states.pkl` (not process-aware).

    This test forces process_index=1 and asserts the process-index-specific RNG state filename exists.
    """
    acc = Accelerator(cpu=True)
    acc.state.process_index = 1

    # Register at least one model so save_state runs through normal paths.
    model = torch.nn.Linear(2, 2)
    acc.prepare(model)

    with tempfile.TemporaryDirectory() as tmpdir:
        acc.save_state(tmpdir)
        files = set(os.listdir(tmpdir))

        expected = f"random_states_{acc.state.process_index}.pkl"
        assert (
            expected in files
        ), f"save_state should write RNG state per-process as {expected!r} when process_index={acc.state.process_index}, but directory contains: {sorted(files)}"