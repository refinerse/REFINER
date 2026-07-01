import re


def test_transformers_import_is_not_at_module_top_level():
    """
    `transformers` is an optional dependency; the module should not import it
    at top-level (e.g., `from transformers import AutoTokenizer`), and should
    instead import it inside the function/method that needs it.
    """
    path = "/workspace/xinference/model/llm/vllm/core.py"
    source = open(path, "r", encoding="utf-8").read()

    # Fail if there is any top-level import from transformers.
    # ("top-level" meaning it begins at column 0; imports inside functions are indented.)
    top_level_transformers_imports = re.findall(
        r"(?m)^(?:from\s+transformers\s+import\s+.+|import\s+transformers(?:\s+as\s+\w+)?)\s*$",
        source,
    )

    assert (
        not top_level_transformers_imports
    ), (
        "Expected no top-level imports from optional dependency 'transformers' in "
        f"{path}. Found top-level import(s): {top_level_transformers_imports}. "
        "Move the import inside the function/method that needs it."
    )