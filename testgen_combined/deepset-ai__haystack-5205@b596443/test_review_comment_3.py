import re


def test_sagemaker_base_removed_type_ignore_on_prompt_handler_call():
    source = open("/workspace/haystack/nodes/prompt/invocation_layer/sagemaker_base.py", encoding="utf-8").read()

    assert (
        "resize_info = self.prompt_handler(prompt)  # type: ignore" not in source
    ), "Expected the prompt_handler call to no longer use '# type: ignore' (should be removed/refactored)."

    # Ensure we still call prompt_handler with the prompt (without type ignore), so we aren't just deleting the line.
    assert re.search(r"^\s*resize_info\s*=\s*self\.prompt_handler\(prompt\)\s*$", source, flags=re.M), (
        "Expected a plain call 'resize_info = self.prompt_handler(prompt)' without '# type: ignore'. "
        "This verifies the refactor removed the ignore rather than removing the behavior."
    )