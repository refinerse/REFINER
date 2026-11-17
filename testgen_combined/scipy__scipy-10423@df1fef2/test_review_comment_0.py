import re

import pytest


def test_pocketfft_version_md_no_scipychanges_patch_and_updated_commit():
    path = "/workspace/scipy/fft/_pocketfft/version.md"
    source = open(path, encoding="utf-8").read()

    assert "With the changes in `scipychanges.patch`" not in source, (
        "version.md should not mention applying `scipychanges.patch`; "
        "SciPy vendors pypocketfft directly at a specific upstream commit."
    )

    m = re.search(r"^\s*commit\s+([0-9a-f]{40})\s*$", source, flags=re.MULTILINE)
    assert m, "version.md must contain a 40-hex commit line like: 'commit <sha>'"
    assert (
        m.group(1) == "cd58e6a1da24ccc2571b998c9f83374e7d9ed783"
    ), "version.md should reference the updated vendored pypocketfft commit SHA"