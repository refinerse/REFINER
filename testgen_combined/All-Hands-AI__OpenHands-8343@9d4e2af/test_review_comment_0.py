import re


def test_agent_cls_overrides_settings_agent_logic_present_in_source():
    source = open("/workspace/openhands/cli/main.py", "r", encoding="utf-8").read()

    # We want to ensure the CLI logic explicitly prioritizes args.agent_cls over settings.agent.
    # AFTER code has:
    #   if args.agent_cls:
    #       config.default_agent = str(args.agent_cls)
    #   else:
    #       assert settings.agent is not None
    #       config.default_agent = settings.agent
    #
    # BEFORE code lacks the explicit "if args.agent_cls" branch and instead only sets the
    # default agent when args.agent_cls is not provided, casting settings.agent to str.
    #
    # This test intentionally source-inspects because importing openhands.cli.main fails
    # in this environment due to missing prompt_toolkit.
    required_patterns = [
        r"\bif\s+args\.agent_cls\s*:\s*\n\s*config\.default_agent\s*=\s*str\(\s*args\.agent_cls\s*\)",
        r"\belse\s*:\s*\n\s*#\s*settings\.agent\s+is\s+not\s+None.*\n\s*assert\s+settings\.agent\s+is\s+not\s+None\s*\n\s*config\.default_agent\s*=\s*settings\.agent\b",
    ]
    for pat in required_patterns:
        assert re.search(pat, source, re.MULTILINE), (
            "Expected main.py to explicitly set config.default_agent from args.agent_cls when provided, "
            "and otherwise assert settings.agent is not None and assign settings.agent directly. "
            f"Missing pattern: {pat}"
        )

    # Guard against the old behavior: only setting from settings.agent when args.agent_cls is absent
    # and always casting settings.agent to str.
    assert "if not args.agent_cls and settings.agent is not None" not in source, (
        "main.py still contains the old conditional 'if not args.agent_cls and settings.agent is not None', "
        "which indicates args.agent_cls is not explicitly prioritized as intended."
    )
    assert "config.default_agent = str(settings.agent)" not in source, (
        "main.py still casts settings.agent to str when setting default_agent; "
        "the updated logic should assign settings.agent directly (after asserting non-None)."
    )