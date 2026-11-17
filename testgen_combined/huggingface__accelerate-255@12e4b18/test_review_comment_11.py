import inspect

import tests.test_state_checkpointing as tsc


def test_training_is_wrapped_in_train_function():
    """
    Structural expectation from review: the repeated training loop is wrapped in a reusable `train` function.

    This test is intentionally structural-but-functional: it imports the module and asserts that a
    top-level callable named `train` exists (so tests/scripts can reuse it rather than duplicating loops).
    """
    assert hasattr(
        tsc, "train"
    ), "Expected tests.test_state_checkpointing to define a top-level `train(...)` helper wrapping the training loop."
    assert callable(tsc.train), "`train` exists but is not callable."

    sig = inspect.signature(tsc.train)
    for name in ["num_epochs", "model", "dataloader", "optimizer", "accelerator"]:
        assert (
            name in sig.parameters
        ), f"`train` should accept parameter `{name}` (signature was: {sig})."