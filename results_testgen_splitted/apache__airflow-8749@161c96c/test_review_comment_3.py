import re


def test_step_function_hook_describe_execution_has_dict_return_annotation():
    """
    The review comment requested documenting the return type via a return annotation:
        def describe_execution(self, execution_arn: str) -> dict:

    This test inspects the source directly (module import is not possible in this env).
    """
    source_path = "/workspace/airflow/providers/amazon/aws/hooks/step_function.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Must include the return annotation for describe_execution.
    # Before code: def describe_execution(self, execution_arn: str):
    # After code:  def describe_execution(self, execution_arn: str) -> dict:
    pattern = r"def\s+describe_execution\s*\(\s*self\s*,\s*execution_arn\s*:\s*str\s*\)\s*->\s*dict\s*:"
    assert re.search(pattern, source), (
        "Expected StepFunctionHook.describe_execution to have an explicit return type annotation "
        "`-> dict` (i.e. `def describe_execution(self, execution_arn: str) -> dict:`), but it was not found."
    )