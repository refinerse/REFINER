import os
import re


def test_to_stata_note_removed_from_v230_whatsnew():
    # Prevent external pytest plugins (e.g. pytest-qt) from auto-loading and crashing
    # due to missing system libs in this execution environment.
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    source = open("/workspace/doc/source/whatsnew/v2.3.0.rst", encoding="utf-8").read()

    pattern = re.compile(
        r"^\s*-\s*:meth:`DataFrame\.to_stata`\s+no\s+longer\s+throws\s+a\s+``TypeError\('encoding without a string argument'\)``",
        re.MULTILINE,
    )

    assert pattern.search(source) is None, (
        "Expected the DataFrame.to_stata TypeError bullet to be removed from "
        "/workspace/doc/source/whatsnew/v2.3.0.rst (it should be moved to v3.0.0.rst), "
        "but it is still present."
    )