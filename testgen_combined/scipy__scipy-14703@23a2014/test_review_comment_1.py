import re


def test_sampling_hinv_uses_consistent_scientific_notation_for_u_resolution():
    path = "/workspace/doc/source/tutorial/stats/sampling_hinv.rst"
    source = open(path, "r", encoding="utf-8").read()

    # The review change was to replace "1.e-10" with "1e-10" for consistency.
    assert "u_resolution=1.e-10" not in source, (
        "Found 'u_resolution=1.e-10' in sampling_hinv.rst; the extra dot should be "
        "removed to use consistent scientific notation: 'u_resolution=1e-10'."
    )

    assert re.search(r"u_resolution\s*=\s*1e-10\b", source), (
        "Expected sampling_hinv.rst to contain 'u_resolution=1e-10' after the change."
    )