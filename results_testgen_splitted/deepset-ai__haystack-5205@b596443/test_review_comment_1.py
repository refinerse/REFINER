import re


def test_invoke_no_prompt_uses_pytest_raises_match_argument():
    source = open("/workspace/test/prompt/invocation_layer/test_sagemaker_hf_infer.py", "r", encoding="utf-8").read()

    # The review comment changes the test to:
    #   with pytest.raises(ValueError, match="No prompt provided."):
    #       layer.invoke()
    #
    # Before, it used:
    #   with pytest.raises(ValueError) as e:
    #       layer.invoke()
    #       assert e.match("No prompt provided.")
    #
    # We assert the updated, correct pattern exists (and thus the old one doesn't).
    assert (
        re.search(
            r"with\s+pytest\.raises\(\s*ValueError\s*,\s*match\s*=\s*[\"']No prompt provided\.[\"']\s*\)\s*:\s*\n\s*layer\.invoke\(\s*\)",
            source,
            flags=re.MULTILINE,
        )
        is not None
    ), (
        "Expected test to assert the ValueError message via pytest.raises(..., match='No prompt provided.') "
        "and to call layer.invoke() inside the context manager. This should be present after the review change."
    )