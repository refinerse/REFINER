import re


def test_step_function_operator_does_not_manually_xcom_push_execution_output():
    """
    The review removed manual XCom push of 'execution_output' because returning the value
    already pushes it to XCom under 'return_value'.

    This test enforces that the operator no longer calls:
        context['ti'].xcom_push(key='execution_output', value=execution_output)
    """
    source_path = "/workspace/airflow/providers/amazon/aws/operators/step_function_get_execution_output.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Match the old manual XCom push block regardless of whitespace/newlines.
    manual_push_pattern = re.compile(
        r"context\s*\[\s*['\"]ti['\"]\s*\]\s*\.xcom_push\s*\(\s*key\s*=\s*['\"]execution_output['\"]\s*,\s*value\s*=\s*execution_output\s*\)",
        re.MULTILINE | re.DOTALL,
    )

    assert not manual_push_pattern.search(source), (
        "Operator should not manually push XCom with key 'execution_output'. "
        "It should return the execution output instead, relying on Airflow's automatic XCom "
        "push to key 'return_value'."
    )