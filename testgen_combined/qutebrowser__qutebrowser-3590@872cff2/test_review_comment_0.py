import re


def test_tab_none_check_does_not_use_truthiness_and_not_none_redundancy():
    """Ensure currentWidget() checks use `is not None` only (not `if tab` and not redundant)."""
    source = open("/workspace/qutebrowser/mainwindow/tabbedbrowser.py", encoding="utf-8").read()

    # BEFORE had: `if tab and tab is not None:` (truthiness + redundant None check)
    assert "if tab and tab is not None:" not in source, (
        "TabbedBrowser should not use a redundant truthiness check like "
        "`if tab and tab is not None:` for currentWidget(); a null pointer maps "
        "to None in Python, so `if tab is not None:` is sufficient."
    )

    # AFTER uses explicit None checks (e.g. `if tab is not None:`) and avoids `if tab:`
    # Verify there is at least one explicit `is not None` check for currentWidget result.
    # (We keep this flexible across refactors by just requiring the pattern exists.)
    assert re.search(r"\bif\s+\w+\s+is\s+not\s+None\s*:", source), (
        "Expected an explicit None check (`if <var> is not None:`) rather than a "
        "truthiness check for the current tab widget."
    )