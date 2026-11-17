import re


def test_sampling_hinv_typo_corrected_corresponding():
    path = "/workspace/doc/source/tutorial/stats/sampling_hinv.rst"
    source = open(path, encoding="utf-8").read()

    # The review fixes a misspelling in the sentence describing u-direction error:
    # "corressponding" -> "corresponding"
    assert (
        "corressponding" not in source
    ), f"Found misspelling 'corressponding' in {path}; expected it to be corrected to 'corresponding'."

    # Ensure the corrected word is present in that context (near the u-direction error formula).
    pattern = r"u-direction.*?\|U\s*-\s*CDF\(X\)\|.*?approximate percentile corresponding"
    assert re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL), (
        f"Did not find the corrected phrasing with 'approximate percentile corresponding' "
        f"near the u-direction error formula in {path}."
    )