import re


def test_setitem_with_new_columns_shape_check_refactored_to_tuple_compare():
    source = open("/workspace/modin/pandas/indexing.py", "r", encoding="utf-8").read()

    # We want to ensure the shape validation for 2D `item` in `_setitem_with_new_columns`
    # is written in the refactored "tuple compare" style rather than indexing item.shape[0]/[1].
    #
    # Before (should fail this test):
    #   if item.shape[0] != len(self.qc.index) or item.shape[1] != len(col_loc):
    #
    # After (should pass this test):
    #   if item.shape != (len(self.qc.index), len(col_loc)):
    #
    # We locate the relevant `else:` branch after `if len(item.shape) == 1:` and assert
    # it uses tuple-based comparison, and does not use the old indexed-shape check.

    assert "def _setitem_with_new_columns" in source, (
        "Expected indexing helper method `_setitem_with_new_columns` to exist in "
        "/workspace/modin/pandas/indexing.py."
    )

    # Capture the first occurrence of the 2D-shape validation branch inside the method.
    m = re.search(
        r"def _setitem_with_new_columns[\s\S]*?"
        r"if\s+len\(item\.shape\)\s*==\s*1\s*:[\s\S]*?"
        r"else\s*:\s*(?P<branch>[\s\S]*?)\n\s*exist_items\s*=",
        source,
    )
    assert m is not None, (
        "Could not locate the shape-validation logic in `_setitem_with_new_columns` "
        "(expected an `if len(item.shape) == 1: ... else: ...` structure)."
    )

    branch = m.group("branch")

    assert "item.shape !=" in branch, (
        "Expected the 2D-shape validation to compare `item.shape` against a tuple "
        "like `(len(self.qc.index), len(col_loc))`, but it did not. "
        "This indicates the pre-refactor style is still present."
    )
    assert "item.shape[0]" not in branch and "item.shape[1]" not in branch, (
        "Expected the refactored tuple-based shape check (no `item.shape[0]`/`item.shape[1]`), "
        "but found indexed shape access in the 2D-shape validation branch."
    )