import re


def test_vllmvisionmodel_load_does_not_create_tokenizer_and_no_custom_init():
    """
    Review intent: VLLMVisionModel should not add extra tokenizer-only loading logic
    (i.e., should rely on the base model load path rather than adding AutoTokenizer),
    and the special __init__ that only sets _tokenizer should be removed.
    """
    source = open("/workspace/xinference/model/llm/vllm/core.py", "r", encoding="utf-8").read()

    # 1) Ensure VLLMVisionModel exists.
    assert (
        "class VLLMVisionModel(VLLMModel, ChatModelMixin):" in source
    ), "Expected VLLMVisionModel to be defined in core.py"

    # 2) The 'before' version imported AutoTokenizer and used it in VLLMVisionModel.load().
    # The 'after' version removes that tokenizer addition entirely.
    assert (
        "AutoTokenizer.from_pretrained" not in source
    ), (
        "VLLMVisionModel should not create an extra HuggingFace tokenizer in load(); "
        "found AutoTokenizer.from_pretrained usage, which indicates the old behavior."
    )

    # 3) The 'before' version also introduced a custom __init__ to set self._tokenizer = None.
    # The 'after' version removes that custom initializer.
    assert (
        re.search(r"\nclass VLLMVisionModel\(VLLMModel, ChatModelMixin\):\n\s+def __init__\(", source)
        is None
    ), (
        "VLLMVisionModel should not define a custom __init__ just to add a tokenizer; "
        "expected no __init__ method in this class."
    )