import re


def test_assistant_agent_config_uses_singular_workbench_field_name() -> None:
    source = open(
        "/workspace/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py",
        "r",
        encoding="utf-8",
    ).read()

    # The style/API decision from the review is to keep the public config field name singular
    # ("workbench") even if it holds a list internally, and not rename it to "workbenches".
    assert "workbenches:" not in source, (
        "AssistantAgentConfig should not expose a 'workbenches' field name. "
        "Keep the public config key singular ('workbench') to avoid an unnecessary/breaking rename."
    )

    # Ensure the intended singular field exists in AssistantAgentConfig.
    # Use a simple regex to tolerate minor formatting differences.
    assert re.search(r"\bworkbench\s*:\s*List\s*\[\s*ComponentModel\s*\]\s*\|\s*None\s*=\s*None\b", source), (
        "AssistantAgentConfig should define 'workbench: List[ComponentModel] | None = None' "
        "(singular name, list type)."
    )