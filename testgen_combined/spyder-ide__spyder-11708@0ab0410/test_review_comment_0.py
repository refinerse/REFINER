import re


def test_pylintrc_helpers_moved_to_pylint_utils_module():
    """
    Verify pylintgui.py no longer defines pylintrc helper functions and instead
    imports get_pylintrc_path from spyder.plugins.pylint.utils.
    """
    source_path = "/workspace/spyder/plugins/pylint/widgets/pylintgui.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert "from spyder.plugins.pylint.utils import get_pylintrc_path" in source, (
        "Expected pylintgui.py to import get_pylintrc_path from "
        "spyder.plugins.pylint.utils after the refactor."
    )

    assert re.search(r"(?m)^def _find_pylintrc_path\(", source) is None, (
        "Expected _find_pylintrc_path to be moved out of pylintgui.py "
        "(into spyder/plugins/pylint/utils.py) and not defined here."
    )

    assert re.search(r"(?m)^def get_pylintrc_path\(", source) is None, (
        "Expected module-level get_pylintrc_path to be moved out of pylintgui.py "
        "(into spyder/plugins/pylint/utils.py) and not defined here."
    )