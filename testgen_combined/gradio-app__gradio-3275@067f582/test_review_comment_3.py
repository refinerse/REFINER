import re

import pytest


GUIDE_PATH = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"


def test_supabase_install_step_is_concrete_and_imperative():
    """
    The review comment asks to replace vague wording ("typically by running...") with
    a concrete instruction ("Install `supabase` by running...") for step 6.
    This is documentation-only, so we verify the updated phrasing via source inspection.
    """
    source = open(GUIDE_PATH, "r", encoding="utf-8").read()

    # Must include the more explicit, imperative instruction (the "after" behavior).
    assert (
        "Install `supabase` by running the following command in your terminal:"
        in source
    ), (
        "Expected the guide to use explicit installation instructions for step 6 "
        "(i.e., 'Install `supabase` by running the following command in your terminal:'). "
        "This ensures the instruction is not vague."
    )

    # Must NOT retain the vague original wording (the "before" behavior).
    assert (
        "Start by installing `supabase`, typically by running in your terminal:"
        not in source
    ), (
        "Found the old vague wording for step 6 ('typically by running...'). "
        "It should be replaced with an explicit instruction."
    )

    # Additionally ensure step 6 is present and matches the expected instruction style.
    assert re.search(
        r"(?m)^\s*6\\?\.\s+Install\s+`supabase`\s+by\s+running\s+the\s+following\s+command\s+in\s+your\s+terminal:\s*$",
        source,
    ), (
        "Expected step 6 to be numbered and to start with: "
        "'6. Install `supabase` by running the following command in your terminal:'"
    )