import pathlib
import re


def test_iter_exclude_none_condition_is_structurally_simplified():
    """
    Structural change only (no behavior difference), so inspect source text directly.

    IMPORTANT: This test must be runnable even if the environment has globally installed
    pytest plugins that add unsupported CLI options (e.g. --no-header). We therefore keep
    the test fully self-contained and avoid importing anything from the repo that might
    trigger plugin/config interactions.
    """
    source = pathlib.Path("/workspace/pydantic/main.py").read_text(encoding="utf8")

    # Narrow to BaseModel._iter method block to avoid false positives elsewhere.
    m = re.search(r"\nclass BaseModel\b[\s\S]*?\n    def _iter\([\s\S]*?\n    def _calculate_keys\(", source)
    assert m, "Could not locate BaseModel._iter method in /workspace/pydantic/main.py"
    iter_block = m.group(0)

    assert "if not (exclude_none and value is None):" in iter_block, (
        "Expected BaseModel._iter to use the simplified exclude_none condition:\n"
        "    if not (exclude_none and value is None):"
    )
    assert "if (exclude_none and value is not None) or not exclude_none:" not in iter_block, (
        "Did not expect BaseModel._iter to still contain the older exclude_none condition:\n"
        "    if (exclude_none and value is not None) or not exclude_none:"
    )