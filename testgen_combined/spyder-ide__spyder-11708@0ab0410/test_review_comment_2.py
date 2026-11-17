# -*- coding: utf-8 -*-
import re


def test_pylintgui_pylintrc_helpers_moved_to_utils_module():
    source_path = "/workspace/spyder/plugins/pylint/widgets/pylintgui.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert (
        "from spyder.plugins.pylint.utils import get_pylintrc_path" in source
    ), (
        "Expected pylintgui.py to import get_pylintrc_path from "
        "spyder.plugins.pylint.utils after refactor."
    )

    assert "def _find_pylintrc_path" not in source, (
        "pylintgui.py should no longer define _find_pylintrc_path(); "
        "pylintrc discovery helpers should be moved to spyder.plugins.pylint.utils."
    )

    assert re.search(r"^\s*def\s+get_pylintrc_path\s*\(", source, flags=re.M) is None, (
        "pylintgui.py should no longer define a module-level get_pylintrc_path(); "
        "it should import it from spyder.plugins.pylint.utils."
    )

    assert "os.chdir(" not in source, (
        "pylintgui.py should not change the process working directory via os.chdir(); "
        "that logic should not live in this widget module after the refactor."
    )