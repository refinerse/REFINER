import re


def test_supabase_guide_numbered_steps_are_direct_and_consistent():
    path = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"
    source = open(path, "r", encoding="utf-8").read()

    # The review request: make the first numbered step direct/imperative (e.g. "Start by...")
    # rather than starting with "We'll start by...".
    assert "1. We'll start by creating a new project in Supabase." not in source, (
        "Step 1 should not start with 'We'll start by...'. "
        "Move the introductory phrasing out of the bullet and make the step imperative "
        "(e.g., 'Start by creating...')."
    )

    # Ensure step 1 is present and uses the imperative phrasing.
    assert re.search(r"(?m)^\s*1\\\.\s+Start by creating a new project in Supabase\.", source), (
        "Expected step 1 to be rewritten in an imperative style as "
        "'1\\. Start by creating a new project in Supabase.'"
    )