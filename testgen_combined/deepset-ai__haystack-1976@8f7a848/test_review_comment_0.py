import re


def test_augment_squad_signature_keeps_default_model_and_tokenizer_and_order():
    """
    The review comment indicates `augment_squad` unintentionally changed its signature by making
    `model` and `tokenizer` required positional args and placing them before `squad_path`.

    This test enforces the intended API:
      - augment_squad(squad_path, output_path, glove_path=..., model="bert-base-uncased", tokenizer="bert-base-uncased", ...)
      - model/tokenizer MUST have defaults
      - model/tokenizer MUST NOT appear before squad_path/output_path in the function signature
    """
    source = open("/workspace/haystack/utils/augment_squad.py", "r", encoding="utf-8").read()

    m = re.search(r"def\s+augment_squad\s*\((?P<params>[\s\S]*?)\)\s*:", source)
    assert m, "Expected to find `def augment_squad(...)` in /workspace/haystack/utils/augment_squad.py"

    params = m.group("params")
    normalized = re.sub(r"\s+", " ", params).strip()

    # Must start with squad_path and output_path (positional order preserved)
    assert normalized.startswith("squad_path: Path, output_path: Path"), (
        "augment_squad() should start with positional args (squad_path, output_path). "
        f"Got: {normalized}"
    )

    # model and tokenizer must have defaults
    assert 'model: str = "bert-base-uncased"' in normalized, (
        "augment_squad() must provide a default for `model` (to avoid unintended breaking API change). "
        f"Got: {normalized}"
    )
    assert 'tokenizer: str = "bert-base-uncased"' in normalized, (
        "augment_squad() must provide a default for `tokenizer` (to avoid unintended breaking API change). "
        f"Got: {normalized}"
    )

    # Ensure model/tokenizer are not placed before squad_path/output_path
    prefix = normalized.split("squad_path: Path", 1)[0]
    assert "model:" not in prefix and "tokenizer:" not in prefix, (
        "`model`/`tokenizer` must not appear before `squad_path` in augment_squad() signature. "
        f"Prefix before squad_path was: {prefix!r}. Full signature: {normalized}"
    )