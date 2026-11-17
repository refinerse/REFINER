import re


def test_mock_get_task_side_effect_uses_exception_class_not_helper_function():
    """
    Verify the review change: replace `mock_get_task.side_effect = raise_runtime_error`
    with the more elegant `mock_get_task.side_effect = RuntimeError`, removing the need
    for defining `raise_runtime_error`.
    """
    source = open("/workspace/test/prompt/invocation_layer/test_hugging_face.py", "r", encoding="utf-8").read()

    assert (
        "mock_get_task.side_effect = RuntimeError" in source
    ), "Expected `mock_get_task.side_effect = RuntimeError` in test_supports(), per review suggestion."

    assert (
        "mock_get_task.side_effect = raise_runtime_error" not in source
    ), "Did not expect `mock_get_task.side_effect = raise_runtime_error` after applying the review suggestion."

    assert (
        re.search(r"^def\s+raise_runtime_error\s*\(", source, flags=re.MULTILINE) is None
    ), "Did not expect a `raise_runtime_error` helper function to exist after using `side_effect = RuntimeError`."