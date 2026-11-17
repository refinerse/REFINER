import pytest

import pandas.tools.tile as tile


def test_preprocess_for_cut_does_not_contain_redundant_name_none_check():
    """
    The review comment indicates that `if name is None:` inside `_preprocess_for_cut`
    is redundant because `name = None` is defined immediately above.

    This test enforces that the redundant conditional is removed.
    It is a source-level behavioral expectation about the implementation,
    since the redundant check has no runtime effect.
    """
    source = open("/workspace/pandas/tools/tile.py", "r", encoding="utf-8").read()

    assert "def _preprocess_for_cut" in source, "Expected _preprocess_for_cut to exist in tile.py"

    redundant_snippet = "if name is None:\n            name = x.name"
    assert redundant_snippet not in source, (
        "Redundant check `if name is None:` should be removed from _preprocess_for_cut "
        "because `name` is initialized to None immediately above. "
        "Found the old pattern:\n"
        f"{redundant_snippet}"
    )

    # Also verify the simplified expected assignment exists (guarded only by x_is_series).
    assert "name = x.name" in source, (
        "Expected _preprocess_for_cut to still assign `name = x.name` when x is a Series."
    )

    # Ensure module remains importable/usable (functional sanity check).
    assert hasattr(tile, "_preprocess_for_cut"), "pandas.tools.tile should expose _preprocess_for_cut"