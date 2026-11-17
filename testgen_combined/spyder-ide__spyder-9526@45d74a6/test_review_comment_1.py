# This test is intentionally self-contained and avoids importing pytest
# (the execution environment's pytest installation is broken due to an
# incompatible attrs version).
import re


def test_fixture_returns_only_editor():
    """
    Review request: make the fixture return only `editor` (not `(editor, lines_lvls)`).

    We use source inspection because importing Spyder's editor tests requires Qt,
    which isn't available in this environment.
    """
    source_path = "/workspace/spyder/plugins/editor/widgets/tests/test_folding.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert "return editor, lines_lvls" not in source, (
        "Expected the fixture to return only `editor`, but found tuple return "
        "(`return editor, lines_lvls`) in the source."
    )

    assert re.search(r"(?m)^\s*return\s+editor\s*$", source), (
        "Expected the fixture to return only `editor` via a standalone "
        "`return editor` line."
    )