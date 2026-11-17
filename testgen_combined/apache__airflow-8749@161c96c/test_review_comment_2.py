import re


def test_start_execution_has_return_type_annotation_str():
    source_path = "/workspace/airflow/providers/amazon/aws/hooks/step_function.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Ensure we're checking the right function definition.
    assert "def start_execution" in source, f"Expected start_execution to exist in {source_path}"

    # Style change requested: add explicit return type annotation "-> str" to start_execution.
    # Before: def start_execution(...):
    # After:  def start_execution(...) -> str:
    pattern = re.compile(r"def\s+start_execution\s*\(.*?\)\s*->\s*str\s*:", re.DOTALL)
    assert pattern.search(source), (
        "Expected StepFunctionHook.start_execution to declare an explicit return type "
        "annotation '-> str' in its function signature."
    )