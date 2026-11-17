import io
import re


def test_pylintgui_refactors_pylintrc_lookup_into_utils_module():
    file_path = "/workspace/spyder/plugins/pylint/widgets/pylintgui.py"
    with io.open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert (
        "from spyder.plugins.pylint.utils import get_pylintrc_path" in source
    ), (
        "Expected pylintgui.py to import get_pylintrc_path from "
        "spyder.plugins.pylint.utils (refactor to shared utility)."
    )

    assert not re.search(r"^[ \t]*def[ \t]+get_pylintrc_path[ \t]*\(", source, flags=re.M), (
        "pylintgui.py should no longer define a local get_pylintrc_path(); "
        "it should use the shared implementation from spyder.plugins.pylint.utils."
    )

    assert not re.search(r"^[ \t]*def[ \t]+_find_pylintrc_path[ \t]*\(", source, flags=re.M), (
        "pylintgui.py should no longer define a local _find_pylintrc_path() helper."
    )

    assert "pylint.config.find_pylintrc" not in source, (
        "pylintgui.py should not directly reference pylint.config.find_pylintrc; "
        "that logic should live in spyder.plugins.pylint.utils."
    )