import re

import pytest


def test_markdown_numbered_steps_use_escaped_period_to_prevent_renumbering_in_html():
    """
    The guide uses a single continuous numbered sequence across sections.
    To prevent Markdown renderers from restarting numbering, steps should be written as `1\.`, `2\.`, etc.
    """
    path = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"
    source = open(path, "r", encoding="utf-8").read()

    # We expect at least steps 1 through 10, each formatted with an escaped dot (e.g., "1\. ").
    # Before fix: steps are "1.", "2.", ... which will not match.
    missing = []
    for i in range(1, 11):
        if re.search(rf"(?m)^\s*{i}\\\.\s+", source) is None:
            missing.append(i)

    assert not missing, (
        "Expected the guide to escape the period in numbered steps to keep numbering stable in HTML "
        f"(e.g., '1\\.', '2\\.'...). Missing escaped numbering for steps: {missing}. "
        "This should fail on the old version that used '1.'/'2.' and pass once updated to '1\\.'/etc."
    )