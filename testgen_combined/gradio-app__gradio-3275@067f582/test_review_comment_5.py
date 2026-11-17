import re

import pytest


def test_supabase_guide_has_link_and_fixed_grammar():
    """
    Verifies the review-requested documentation changes:
    1) Supabase is linked to supabase.com (markdown link).
    2) The sentence reads "from Supabase and plot it in" (typo fixed).
    """
    path = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"
    source = open(path, "r", encoding="utf-8").read()

    assert (
        re.search(r"\[Supabase\]\(\s*https?://supabase\.com/?\s*\)", source) is not None
    ), "Guide should link 'Supabase' to https://supabase.com/ (e.g., '[Supabase](https://supabase.com/)')."

    assert (
        "from Supabase and plot it in" in source
    ), "Guide intro should fix grammar to: 'read data from Supabase and plot it in ...' (missing 'and' in before version)."