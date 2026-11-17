import re

GUIDE_PATH = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"


def test_supabase_dashboard_guide_has_fixed_skip_sentence_and_working_anchor_link():
    source = open(GUIDE_PATH, "r", encoding="utf-8").read()

    # 1) Typo fix: ensure the awkward duplicated "sections and first two sections" phrasing is gone
    assert (
        "you can skip sections and first two sections and go" not in source
    ), "Guide still contains the typo 'skip sections and first two sections'; it should read 'skip the first two sections'."

    assert (
        "you can skip the first two sections and go directly to" in source.lower()
    ), "Guide should instruct readers they can 'skip the first two sections and go directly to ...'."

    # 2) Link fix: the 'visualizing the data' link must not have an empty URL
    assert (
        "[visualizing the data]()" not in source
    ), "Guide still contains an empty Markdown link '[visualizing the data]()'; it should link to the visualization section anchor."

    # Ensure the updated link points to the correct section header slug
    m = re.search(r"\[visualizing the data\]\((#[^)]+)\)", source, flags=re.IGNORECASE)
    assert m, "Guide should contain a non-empty Markdown link for '[visualizing the data](#...)'."

    anchor = m.group(1).strip().lower()
    assert (
        anchor == "#visualize-the-data-in-a-real-time-gradio-dashboard"
    ), f"Expected link anchor '#visualize-the-data-in-a-real-time-gradio-dashboard', got {anchor!r}."