import re


def test_metadata_bookkeeping_intro_sentence_style_change():
    """
    Verify the style change requested in the review comment:
    Replace "Here is important information..." with "Important information..."
    under the "Metadata for bookkeeping" section.
    """
    source = open("/workspace/docs/3.0rc/deploy/index.mdx", encoding="utf-8").read()

    # Find the "Metadata for bookkeeping" section and inspect the first non-empty line after it.
    marker = "### Metadata for bookkeeping"
    idx = source.find(marker)
    assert idx != -1, "Expected to find the '### Metadata for bookkeeping' section header."

    after = source[idx + len(marker) :]
    # Take a small window to avoid matching an earlier/later instance by accident
    window = after[:600]

    # Remove leading whitespace/newlines, then take the next non-empty line
    lines = [ln.strip() for ln in window.splitlines()]
    first_nonempty = next((ln for ln in lines if ln), "")

    assert (
        first_nonempty == "Important information for the versions, descriptions, and tags fields:"
    ), (
        "Expected the first non-empty line after '### Metadata for bookkeeping' to be exactly:\n"
        "'Important information for the versions, descriptions, and tags fields:'\n"
        f"Got:\n{first_nonempty!r}\n"
        "This enforces the style change requested in the review comment."
    )

    # Ensure the old phrasing is not present anywhere in this section window
    assert not re.search(
        r"\bHere\s+is\s+important\s+information\s+on\s+the\s+versions,\s+descriptions,\s+and\s+tags\s+fields:",
        window,
    ), (
        "Found the old phrasing 'Here is important information on the versions, descriptions, and tags fields:' "
        "near the 'Metadata for bookkeeping' section; it should be updated to start with "
        "'Important information ...' per the review comment."
    )