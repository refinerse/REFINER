import re


def test_dataframe_explode_ignore_index_has_bool_type_annotation():
    source = open("/workspace/pandas/core/frame.py", encoding="utf-8").read()

    # We want to ensure `ignore_index` is typed as bool in the explode signature.
    # Before: def explode(self, column: Union[str, Tuple], ignore_index=False) -> "DataFrame":
    # After:  def explode(self, column: Union[str, Tuple], ignore_index: bool = False) -> "DataFrame":
    pattern = re.compile(
        r"def\s+explode\s*\(\s*self\s*,\s*column\s*:\s*Union\[\s*str\s*,\s*Tuple\s*\]\s*,"
        r"\s*ignore_index\s*:\s*bool\s*=\s*False\s*\)\s*->\s*['\"]DataFrame['\"]\s*:",
        flags=re.MULTILINE,
    )

    assert pattern.search(source), (
        "DataFrame.explode should type-annotate ignore_index as `bool` with default "
        "`False` in the function signature (i.e., `ignore_index: bool = False`)."
    )