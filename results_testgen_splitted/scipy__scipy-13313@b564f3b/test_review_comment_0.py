import re


def test_qhull_pyi_uses_future_annotations_import():
    """
    The addressed review added `from __future__ import annotations` to the stub.

    This has an observable static-typing impact and is the main functional change
    between the before/after versions that we can reliably test via source inspection
    (SciPy import is unavailable in this environment).
    """
    source = open("/workspace/scipy/spatial/qhull.pyi", encoding="utf-8").read()

    assert (
        "from __future__ import annotations" in source
    ), "Expected qhull.pyi to include `from __future__ import annotations` (added in the fix)."


def test_qhull_pyi_has_multiline_qhull_init_signature():
    """
    The addressed review reformatted the `_Qhull.__init__` signature into a multiline
    form; ensure the updated stub is present.

    This is a robust marker for the updated version without importing SciPy.
    """
    source = open("/workspace/scipy/spatial/qhull.pyi", encoding="utf-8").read()

    # Look for the specific multiline def header introduced after the change.
    pattern = r"class _Qhull:\s*\n\s*def __init__\(\s*\n"
    assert re.search(pattern, source), (
        "Expected qhull.pyi to define `_Qhull.__init__` using the multiline signature "
        "format introduced in the updated stub."
    )