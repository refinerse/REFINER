import re


def test_start_execution_uses_response_get_for_execution_arn():
    """
    The review requested simplifying:
        return response['executionArn'] if 'executionArn' in response else None
    to:
        return response.get('executionArn')   (or explicitly with default None)

    We verify the new, more explicit pattern exists in the source.
    """
    source = open("/workspace/airflow/providers/amazon/aws/hooks/step_function.py").read()

    # Must use dict.get for executionArn (optionally with explicit None default).
    assert (
        "response.get('executionArn')" in source
        or "response.get('executionArn', None)" in source
    ), (
        "StepFunctionHook.start_execution should return the executionArn via "
        "response.get('executionArn') (or response.get('executionArn', None)) "
        "as per the review comment, instead of a conditional membership check."
    )

    # Ensure the old conditional-return pattern is not present.
    old_pattern = r"return\s+response\['executionArn'\]\s+if\s+'executionArn'\s+in\s+response\s+else\s+None"
    assert not re.search(old_pattern, source), (
        "Old pattern still present: "
        "return response['executionArn'] if 'executionArn' in response else None. "
        "It should be replaced by response.get('executionArn', None)."
    )