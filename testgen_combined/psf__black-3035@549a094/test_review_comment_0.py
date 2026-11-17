import re


def test_changes_entry_moved_to_preview_style_and_reworded():
    source = open("/workspace/CHANGES.md", encoding="utf8").read()

    # The review requires this change to be in Preview style, not stable Style.
    # So "Style" section must NOT contain the PR #3035 entry.
    style_section_match = re.search(
        r"^### Style\s*\n(?P<body>.*?)(?=^### )",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert style_section_match, "Expected to find a '### Style' section in /workspace/CHANGES.md"
    style_body = style_section_match.group("body")
    assert (
        "#3035" not in style_body
    ), "PR #3035 changelog entry must not be listed under the stable '### Style' section"

    # And "Preview style" section MUST contain the PR #3035 entry with the updated wording.
    preview_section_match = re.search(
        r"^### Preview style\s*\n(?P<body>.*?)(?=^### )",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert (
        preview_section_match
    ), "Expected to find a '### Preview style' section in /workspace/CHANGES.md"
    preview_body = preview_section_match.group("body")
    assert (
        "- Remove trailing newlines after code block open (#3035)" in preview_body
    ), "Expected PR #3035 to be recorded under '### Preview style' with the updated wording"