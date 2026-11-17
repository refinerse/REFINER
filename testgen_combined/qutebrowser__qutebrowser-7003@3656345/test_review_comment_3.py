import re


def test_downloads_feature_uses_tmpdir_replacement_for_external_fileselector():
    """Ensure the external folder fileselector scenario uses (tmpdir)/(dirsep)
    placeholders instead of a hardcoded repo path, so it points to a well-defined
    temporary downloads directory.
    """
    path = "/workspace/tests/end2end/features/downloads.feature"
    source = open(path, encoding="utf-8").read()

    # The review comment requested using a well-defined directory via placeholders:
    # "(tmpdir)(dirsep)downloads(dirsep)subdir"
    assert (
        'And I setup a fake folder fileselector selecting "(tmpdir)(dirsep)downloads(dirsep)subdir" and writes to a temporary file'
        in source
    ), (
        "Expected the downloads.feature external fileselector setup step to use "
        "the '(tmpdir)(dirsep)downloads(dirsep)subdir' placeholders as suggested "
        "in the review comment, but it was not found."
    )

    # Ensure we no longer use the old hardcoded path which is not tmpdir-based.
    assert (
        'And I setup a fake folder fileselector selecting "tests/end2end/data/backforward/" and writes to a temporary file'
        not in source
    ), (
        "Found the old hardcoded path 'tests/end2end/data/backforward/' in the "
        "external fileselector setup step. The review requested using a tmpdir-based "
        "path to avoid relying on the default directory."
    )