import inspect
import pytest

import haystack.components.agents.agent as agent_module


def test_run_async_select_streaming_callback_requires_async_true():
    """
    The Agent.run_async method must call select_streaming_callback(..., requires_async=True)
    so that async-only callbacks are accepted in async execution.
    """
    source = inspect.getsource(agent_module.Agent.run_async)

    assert "select_streaming_callback" in source, "Sanity check: Agent.run_async should use select_streaming_callback()."

    assert (
        "requires_async=True" in source
    ), "Agent.run_async must pass requires_async=True to select_streaming_callback() (before code uses False)."