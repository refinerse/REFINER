import pytest

from haystack.components.tools.tool_invoker import ToolInvoker
from haystack.dataclasses import ChatMessage, ToolCall
from haystack.tools import Tool


def test_streaming_callback_receives_tool_result_and_tool_call_and_fires_after_invoke():
    """
    Review intent: streaming_callback should receive the tool output in a structured way
    (meta contains 'tool_result' and 'tool_call'), not the older shape.

    This reliably distinguishes:
    - BEFORE: callback is invoked via _stream_tool_result() with meta containing "tool_calls" (and content=result)
    - AFTER: callback is invoked with StreamingChunk(content="", meta={"tool_result": ..., "tool_call": ...})

    We also assert the callback is invoked after the tool is successfully invoked by checking
    the tool function was executed (side-effect) before the callback fires.
    """

    invoked = {"count": 0}

    def add(a: int, b: int) -> int:
        invoked["count"] += 1
        return a + b

    tool = Tool(
        name="adder",
        description="adds two integers",
        function=add,
        parameters={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )

    tool_call = ToolCall(tool_name="adder", arguments={"a": 1, "b": 2}, id="call-1")
    msg = ChatMessage.from_assistant(tool_calls=[tool_call])

    callback_observed_invoked_count = []
    received_chunks = []

    def streaming_callback(chunk):
        callback_observed_invoked_count.append(invoked["count"])
        received_chunks.append(chunk)

    invoker = ToolInvoker(tools=[tool])
    result = invoker.run(messages=[msg], streaming_callback=streaming_callback)

    assert invoked["count"] == 1, "Sanity check: expected tool to be invoked exactly once."
    assert len(received_chunks) == 1, "Expected exactly one streaming callback invocation for one tool call."
    assert callback_observed_invoked_count == [
        1
    ], "streaming_callback should be invoked only after the tool function has been invoked."

    chunk = received_chunks[0]
    assert hasattr(chunk, "meta"), "streaming_callback must receive a StreamingChunk-like object with .meta."

    assert "tool_result" in chunk.meta and "tool_call" in chunk.meta, (
        "Expected streaming_callback to receive StreamingChunk.meta with keys 'tool_result' and 'tool_call' "
        "(the new structured contract)."
    )
    assert "tool_calls" not in chunk.meta, (
        "Did not expect legacy 'tool_calls' metadata shape; callback should receive tool_result/tool_call instead."
    )

    assert chunk.meta["tool_result"] == 3, "Expected streamed tool_result to match actual tool invocation result."
    assert chunk.meta["tool_call"].tool_name == "adder", "Expected streamed tool_call to match the invoked tool call."

    # Keep a light check that the tool result message still exists in the run output.
    assert len(result["tool_messages"]) == 1, "Expected one tool message for one tool call."
    tool_msg = result["tool_messages"][0]
    assert tool_msg.is_from_tool, "Expected returned message to be a tool ChatMessage."