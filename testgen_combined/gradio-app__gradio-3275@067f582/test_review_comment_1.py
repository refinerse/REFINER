import re

GUIDE_PATH = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"


def test_removed_unnecessary_some_before_fake_commerce_data():
    source = open(GUIDE_PATH, "r", encoding="utf-8").read()

    # The review comment requests removing "some:" (i.e., "some fake commerce data")
    # in favor of "fake commerce data".
    assert (
        "we'll create some fake commerce data and put it in Supabase" not in source
    ), (
        "Guide still contains unnecessary 'some' in the sentence about creating fake commerce data. "
        "Expected phrasing without 'some' (e.g., \"we'll create fake commerce data and put it in Supabase\")."
    )

    assert re.search(
        r"we'll create fake commerce data and put it in Supabase",
        source,
        flags=re.IGNORECASE,
    ), (
        "Guide should say it will 'create fake commerce data and put it in Supabase' "
        "(without 'some') to reflect the structural edit."
    )