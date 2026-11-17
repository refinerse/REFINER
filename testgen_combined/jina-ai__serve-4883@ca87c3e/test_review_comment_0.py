import re


def test_retries_default_and_help_text_are_updated():
    source = open("/workspace/jina/parsers/orchestrate/pod.py", "r", encoding="utf-8").read()

    # Ensure the --retries argument exists (sanity check for both versions)
    assert "--retries" in source, "Expected pod parser to define a '--retries' CLI argument"

    # The reviewed change: default must be -1 (not None) and the help text must not mention None anymore.
    assert re.search(r"default\s*=\s*-1\b", source), (
        "Expected '--retries' to default to -1 (sentinel for 'use policy default'), "
        "but did not find 'default=-1' in /workspace/jina/parsers/orchestrate/pod.py"
    )

    assert "If None or <0" not in source, (
        "Help text for '--retries' should not mention None anymore; "
        "expected semantics: 'If <0 it defaults to max(3, num_replicas)'"
    )

    assert "If <0 it defaults to max(3, num_replicas)" in source, (
        "Expected updated help text for '--retries' to be: "
        "'If <0 it defaults to max(3, num_replicas)'"
    )