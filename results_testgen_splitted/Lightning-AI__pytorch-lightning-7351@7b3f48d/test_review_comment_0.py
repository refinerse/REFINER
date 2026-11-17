import re


def _get_property_body(source: str, prop_name: str) -> str:
    # Capture the property body up to the next top-level "def" with the same indentation level
    m = re.search(
        rf"@property\s+def\s+{re.escape(prop_name)}\([^)]*\)\s*->\s*Optional\[int\]\s*:\s*(?P<body>.*?)(?=\n\s*def\s+|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert m is not None, f"Expected to find the `{prop_name}` property definition in logger_connector.py"
    return m.group("body")


def test_logger_connector_evaluation_log_step_explicit_else_return_none():
    source = open(
        "/workspace/pytorch_lightning/trainer/connectors/logger_connector/logger_connector.py",
        encoding="utf-8",
    ).read()

    body = _get_property_body(source, "evaluation_log_step")

    # The fixed version includes an explicit else clause:
    #     else:
    #         return None
    # The "before" version did not have it.
    assert (
        re.search(r"\n\s*else:\s*\n\s*return\s+None\s*$", body, flags=re.MULTILINE) is not None
    ), (
        "The `evaluation_log_step` property must explicitly handle non-validation/testing stages with an "
        "`else: return None` clause."
    )


def test_logger_connector_log_evaluation_step_metrics_has_explicit_return_annotation():
    source = open(
        "/workspace/pytorch_lightning/trainer/connectors/logger_connector/logger_connector.py",
        encoding="utf-8",
    ).read()

    # The review suggestion requests adding `-> None` on the method signature.
    assert (
        re.search(r"\n\s*def\s+log_evaluation_step_metrics\(\s*self\s*\)\s*->\s*None\s*:", source) is not None
    ), (
        "Expected `log_evaluation_step_metrics` to have an explicit return annotation `-> None` in its signature."
    )