import re


def test_supabase_signup_link_is_clickable_markdown():
    source_path = "/workspace/guides/05_tabular-data-science-and-plots/creating-a-dashboard-from-supabase-data.md"
    source = open(source_path, "r", encoding="utf-8").read()

    clickable = "[https://app.supabase.com/](https://app.supabase.com/)"
    assert (
        clickable in source
    ), (
        "Expected the Supabase signup URL to be a clickable Markdown link, exactly:\n"
        f"  {clickable}\n"
        "But the guide does not contain that Markdown link (it may still be plain text)."
    )

    # Ensure the old, non-clickable form is not present as the prerequisites signup link.
    # (We check for the exact old sentence fragment to avoid false failures.)
    old_plain = "sign up for here: https://app.supabase.com/"
    assert (
        old_plain not in source
    ), (
        "Found the old non-clickable prerequisites link text:\n"
        f"  {old_plain}\n"
        "The guide should use a clickable Markdown link instead."
    )

    # Sanity check: there should be at least one Markdown link to app.supabase.com in the file.
    assert re.search(r"\]\(https://app\.supabase\.com/\)", source), (
        "Expected at least one Markdown link target '(https://app.supabase.com/)' "
        "to ensure the URL is actually linked."
    )