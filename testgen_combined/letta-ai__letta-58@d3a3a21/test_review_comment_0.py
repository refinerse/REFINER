import re


def test_initialize_message_sequence_boot_messages_are_model_dependent():
    source = open("/workspace/memgpt/agent.py", "r", encoding="utf-8").read()

    # The review comment asks that boot message selection depend on the model.
    # We enforce two observable source-level requirements:
    #  1) initialize_message_sequence takes a `model` parameter
    #  2) boot messages switch based on whether model includes "gpt-3.5"
    assert "def initialize_message_sequence(" in source, "Expected initialize_message_sequence to exist in /workspace/memgpt/agent.py"

    # 1) Signature includes model
    sig_match = re.search(r"def\s+initialize_message_sequence\s*\((.*?)\)\s*:", source, flags=re.S)
    assert sig_match, "Could not locate initialize_message_sequence(...) signature"
    sig_args = sig_match.group(1)
    assert re.search(r"(^|[\s,])model([\s,]|$)", sig_args), (
        "initialize_message_sequence should accept a `model` parameter so boot message choice can be model-dependent"
    )

    # 2) Model-dependent selection between gpt-3.5 and default
    assert "if 'gpt-3.5' in model" in source, (
        "Expected model-dependent boot message selection: `if 'gpt-3.5' in model:`"
    )
    assert "get_initial_boot_messages('startup_with_send_message_gpt35')" in source, (
        "Expected GPT-3.5-specific boot messages: get_initial_boot_messages('startup_with_send_message_gpt35')"
    )
    assert "get_initial_boot_messages('startup_with_send_message')" in source, (
        "Expected non-GPT-3.5 default boot messages: get_initial_boot_messages('startup_with_send_message')"
    )