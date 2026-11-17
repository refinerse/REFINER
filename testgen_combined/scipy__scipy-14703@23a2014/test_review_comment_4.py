import re


def test_sampling_hinv_grammar_fix_higher_orders_sentence():
    source = open("/workspace/doc/source/tutorial/stats/sampling_hinv.rst", encoding="utf-8").read()

    bad = "Higher orders result is fewer number of intervals:"
    good = "Higher orders result in a fewer number of intervals:"

    assert bad not in source, (
        "The documentation should not contain the ungrammatical sentence "
        f"{bad!r}; it should be replaced with {good!r}."
    )
    assert good in source, (
        "The documentation should contain the corrected sentence "
        f"{good!r} (as per the review comment fix)."
    )

    # Ensure the corrected sentence appears exactly once to avoid mixed versions.
    assert len(re.findall(re.escape(good), source)) == 1, (
        "Expected the corrected sentence to appear exactly once in the document."
    )