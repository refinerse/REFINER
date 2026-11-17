import re


def test_contextlevel_disallow_dml_is_optional_str_and_defaults_to_none():
    source = open("/workspace/edb/edgeql/compiler/context.py", "r").read()

    # The review requested: make disallow_dml Optional[str] so it can carry
    # a context message like "in a FILTER clause".
    assert (
        "disallow_dml: Optional[str]" in source
    ), (
        "ContextLevel.disallow_dml should be annotated as Optional[str] "
        "(so it can carry a contextual message); expected to find "
        "'disallow_dml: Optional[str]' in /workspace/edb/edgeql/compiler/context.py"
    )

    # And when a new root context level is created, it should default to None
    # (meaning DML is allowed; if disallowed, it should be a string message).
    assert re.search(r"\bself\.disallow_dml\s*=\s*None\b", source), (
        "ContextLevel.__init__ should default disallow_dml to None for a new "
        "context level; expected to find 'self.disallow_dml = None' in "
        "/workspace/edb/edgeql/compiler/context.py"
    )