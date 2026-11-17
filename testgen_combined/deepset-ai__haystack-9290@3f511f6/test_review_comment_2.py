import inspect

import pytest

from haystack.components.agents.agent import Agent


def test_agent_init_does_not_expose_stream_tool_result_parameter():
    """
    The review decision was to DROP the `stream_tool_result` init parameter and make tool-result streaming
    controlled solely by the user's streaming callback.

    This test asserts that Agent.__init__ no longer accepts `stream_tool_result`.
    - FAILS on the "before" code where the parameter exists.
    - PASSES on the "after" code where the parameter is removed.
    """
    sig = inspect.signature(Agent.__init__)
    assert (
        "stream_tool_result" not in sig.parameters
    ), "Agent.__init__ should not accept `stream_tool_result`; tool-result streaming must be controlled only via streaming_callback."