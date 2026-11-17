import re


def test_hinv_docstring_uses_correct_corresponding_in_u_error_sentence():
    """
    Source-level regression test for the reviewed docstring change:
    in the HINV docstring's u-error sentence, "corresponding" should be spelled
    correctly in the specific phrase.

    The repository may still contain the old misspelling elsewhere (e.g. in
    other docstrings), so we only test the relevant sentence fragment.
    """
    path = "/workspace/scipy/stats/_unuran/unuran_wrapper.pyx.templ"
    source = open(path, "r", encoding="utf-8").read()

    # Narrow to the HINV docstring area to avoid matching unrelated content.
    hinv_pos = source.find("cdef class NumericalInverseHermite(Method):")
    assert hinv_pos != -1, "Sanity check: NumericalInverseHermite definition not found."

    # Take a window starting at the class definition; should include docstring.
    window = source[hinv_pos : hinv_pos + 12000]

    # Ensure we are looking at the right sentence from the review hunk.
    assert "maximal numerical error in \"u-direction\"" in window, (
        "Sanity check: expected HINV docstring u-error description not found."
    )

    # Key behavioral/documentation requirement: corrected spelling in the target phrase.
    assert "approximate percentile corresponding to the" in window, (
        "Expected HINV docstring to contain the corrected phrase "
        "'approximate percentile corresponding to the' in the u-error description."
    )

    # Also ensure the u-error math expression fragment from the review is present nearby.
    assert re.search(r"``\|U\s*-\s*CDF\(X\)\|``", window), (
        "Expected the u-error math expression ``|U - CDF(X)|`` in the HINV docstring."
    )