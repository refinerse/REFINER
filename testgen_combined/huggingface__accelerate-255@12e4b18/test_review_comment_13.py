import importlib

import tests.test_state_checkpointing as mod


def test_state_checkpointing_is_structured_as_proper_test_not_script():
    """
    The reviewed change converts a script-style "test" (requiring CLI args and a main())
    into a proper test case collected by pytest/unittest.

    This test checks only the structural/runtime-import aspects (not the checkpointing
    implementation details), so it remains robust across PyTorch serialization changes.
    """
    importlib.reload(mod)

    # AFTER: no top-level pytest test function that requires custom args.
    # BEFORE: module defines `test_can_resume_training(args)` at top-level.
    assert not hasattr(
        mod, "test_can_resume_training"
    ), "Expected no top-level `test_can_resume_training(args)` function; it should be a proper test method on a TestCase."

    # AFTER: unittest-style test container exists.
    assert hasattr(mod, "CheckpointTest"), "Expected `CheckpointTest` to exist after refactor."
    cls = mod.CheckpointTest
    assert hasattr(cls, "test_can_resume_training") and callable(
        getattr(cls, "test_can_resume_training")
    ), "Expected `CheckpointTest.test_can_resume_training` test method to exist and be callable."

    # BEFORE: script entrypoint exists and is invoked under __main__.
    # AFTER: no `main()` script entrypoint.
    assert not hasattr(mod, "main"), "Expected no script-style `main()` in a test module after refactor."