import os
import tempfile

import torch

from src.accelerate.accelerator import Accelerator


def test_save_state_uses_central_checkpointing_helpers_and_returns_value():
    """
    Style/API expectation from review: Accelerator.save_state should not implement its own per-model file naming logic
    (which previously contained an indexing condition bug), but should delegate to the shared checkpointing helpers.

    Runtime-observable check:
    - In the fixed version, save_state returns the value of save_accelerator_state (a non-None dict).
    - In the old version, save_state returns None.
    """
    acc = Accelerator(cpu=True)

    # Register two models to ensure the old buggy naming code path would have been exercised.
    m1, m2 = torch.nn.Linear(2, 2), torch.nn.Linear(2, 2)
    acc.prepare(m1, m2)

    with tempfile.TemporaryDirectory() as tmpdir:
        out = acc.save_state(tmpdir)

        assert out is not None, (
            "Accelerator.save_state() is expected to delegate to the shared checkpointing helper and return its "
            "result (non-None). Returning None indicates the old inline implementation is still used."
        )

        # Basic sanity that something got written; avoids relying on exact filenames.
        assert os.path.isdir(tmpdir), "Output directory should exist after save_state()."
        assert len(os.listdir(tmpdir)) > 0, "save_state() should create at least one file in the output directory."