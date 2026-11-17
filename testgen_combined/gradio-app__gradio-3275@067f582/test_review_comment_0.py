import re


def test_supabase_dashboard_guide_has_direct_link_to_visualize_section():
    """
    Ensures the guide's "skip ahead" sentence links directly to the visualization section,
    rather than using an empty markdown link target.
    """
    path = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"
    source = open(path, "r", encoding="utf-8").read()

    # The review asks to "go directly to [visualizing the data](#...)" rather than "[visualizing the data]()".
    assert "[visualizing the data](" in source, (
        "Expected the guide to contain a markdown link with anchor text 'visualizing the data'."
    )

    assert "[visualizing the data]()" not in source, (
        "The guide still contains an empty markdown link target '[visualizing the data]()'. "
        "It should link directly to the visualization section (e.g. "
        "'[visualizing the data](#visualize-the-data-in-a-real-time-gradio-dashboard)')."
    )

    # Also verify it's specifically an in-page anchor link (most direct form requested).
    assert re.search(r"\[visualizing the data\]\(\s*#.+\)", source), (
        "Expected '[visualizing the data]' to link to an in-page anchor (e.g. '(#visualize-...)'), "
        "so readers can skip directly to the visualization section."
    )