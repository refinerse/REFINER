import re


def test_column_transformer_set_output_docstring_none_semantics():
    source = open("/workspace/sklearn/compose/_column_transformer.py", "r", encoding="utf-8").read()

    # The review reverted a docstring change: for ColumnTransformer.set_output,
    # `transform=None` should mean "configuration is unchanged" and should NOT
    # claim that the "global configuration is used".
    before_phrase = "`None`: Transform configuration is unchanged, global configuration is used"
    after_phrase = "`None`: Transform configuration is unchanged"

    assert before_phrase not in source, (
        "ColumnTransformer.set_output docstring should not claim that `transform=None` "
        "uses the global configuration; it should only say that the configuration is unchanged."
    )

    # Ensure the intended (reverted) wording is present (and specifically in the set_output docstring
    # area, not elsewhere).
    m = re.search(r"def set_output\(self,\s*\*,\s*transform=None\):([\s\S]{0,1200})", source)
    assert m is not None, "Expected to find ColumnTransformer.set_output method definition in source."

    set_output_block = m.group(1)
    assert after_phrase in set_output_block, (
        "Expected ColumnTransformer.set_output docstring to include the bullet: "
        "`None`: Transform configuration is unchanged"
    )