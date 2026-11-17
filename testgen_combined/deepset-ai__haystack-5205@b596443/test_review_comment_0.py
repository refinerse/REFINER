import re


def test_sagemaker_check_aws_connect_uses_raise_from_for_exception_chaining():
    source = open("/workspace/haystack/nodes/prompt/invocation_layer/sagemaker_base.py", "r", encoding="utf-8").read()

    # We verify the behavior requested in the review: exception chaining via `raise ... from e`
    # in the BotoCoreError handler inside `check_aws_connect`.
    #
    # "Before" code raises SageMakerConfigurationError(...) without `from e` and embeds the cause in the message.
    # "After" code raises SageMakerConfigurationError(...) `from e` and does NOT append "The root cause is: {e}".
    assert "def check_aws_connect" in source, "Sanity check: expected check_aws_connect() to exist in the file."

    raise_from_pattern = re.compile(
        r"except\s+BotoCoreError\s+as\s+e\s*:\s*.*?raise\s+SageMakerConfigurationError\s*\(.*?\)\s*from\s+e",
        re.DOTALL,
    )
    assert raise_from_pattern.search(source), (
        "Expected check_aws_connect() to re-raise SageMakerConfigurationError using exception chaining "
        "(`raise ... from e`) when catching BotoCoreError. This should be present after the review change."
    )

    # Also ensure we are not relying on message concatenation for the root cause in this branch anymore.
    # (This was part of the refactor in the PR that introduced `raise ... from e`.)
    assert "The root cause is:" not in source, (
        "Did not expect the error message to include 'The root cause is:' after switching to pythonic "
        "exception chaining (`raise ... from e`)."
    )