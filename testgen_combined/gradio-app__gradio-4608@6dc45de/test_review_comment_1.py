import re


def test_code_language_literal_does_not_include_none_member():
    source = open("/workspace/gradio/components/code.py", "r", encoding="utf-8").read()

    # The review change ensures that `None` is not included as a member of the
    # Literal[...] list; instead, it should be expressed as `| None` after the Literal.
    # This should hold for BOTH Code.__init__ and Code.update.
    assert (
        "Literal[" in source
    ), "Expected gradio/components/code.py to contain a typing.Literal[...] annotation for language."

    # Grab each language Literal[...] block (there should be one in __init__ and one in update)
    blocks = re.findall(r"language:\s*Literal\[(.*?)\]\s*(?:\|\s*None)?\s*=\s*None", source, flags=re.S)
    assert len(blocks) >= 2, (
        "Expected at least two `language: Literal[...] | None = None` annotations "
        "(one in Code.__init__, one in Code.update)."
    )

    # In the fixed version, the Literal list contains only string members; None is added outside via `| None`.
    for i, block in enumerate(blocks[:2], start=1):
        assert "None" not in block, (
            f"Language Literal block #{i} incorrectly includes `None` as a Literal member. "
            "The type should list only string literals inside Literal[...] and then add `| None` "
            "after the closing bracket."
        )