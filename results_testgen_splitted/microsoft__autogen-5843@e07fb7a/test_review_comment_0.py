import re

SWARM_GROUP_CHAT_PATH = "/workspace/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_swarm_group_chat.py"


def test_swarm_constructor_does_not_require_keyword_only_args_for_optional_params() -> None:
    """
    The review reverted a potentially breaking change: adding '*' to Swarm.__init__
    (which would force termination_condition/max_turns/runtime to be keyword-only).

    This test asserts the reverted (non-breaking) behavior in the source:
    Swarm.__init__ should NOT have a '*' after participants.
    """
    source = open(SWARM_GROUP_CHAT_PATH, "r", encoding="utf-8").read()

    # If the breaking change exists, we'd see:
    # def __init__(..., participants: List[ChatAgent], *, termination_condition=..., ...)
    kw_only_pattern = re.compile(
        r"class\s+Swarm\b[\s\S]*?def\s+__init__\(\s*self\s*,\s*[\s\S]*?"
        r"participants\s*:\s*List\[\s*ChatAgent\s*\]\s*,\s*\*",
        re.MULTILINE,
    )
    assert not kw_only_pattern.search(source), (
        "Swarm.__init__ unexpectedly enforces keyword-only arguments (found a '*' after "
        "participants). The reverted behavior should allow passing termination_condition/max_turns/runtime "
        "positionally (i.e., no '*' in the constructor signature)."
    )