import os


def test_changelog_entry_removed_for_doc_only_change():
    """
    Doc-only change: no changelog entry should be present.
    We assert the changelog entry file was removed (preferred) or is empty (acceptable).
    """
    path = "/workspace/changelog/60880.fixed"

    if not os.path.exists(path):
        assert True, "Changelog entry file was removed as expected for a doc-only change."
        return

    contents = open(path, encoding="utf-8").read()
    assert contents.strip() == "", (
        "Expected the changelog entry file to be removed or empty for a doc-only change. "
        f"File exists and contains non-whitespace content: {contents!r}"
    )