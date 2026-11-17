import re


def test_whatsnew_append_note_mentions_categorical_example():
    source = open("/workspace/doc/source/whatsnew/v0.23.0.txt", encoding="utf-8").read()

    # The review asked to "add the case this is actually addressing (e.g. categorical)".
    # The updated release note should explicitly mention an example using CategoricalIndex.
    pattern = re.compile(
        r"-\s+:meth:`DataFrame\.append`.*\(\s*e\.g\.\s*if both are\s*``CategoricalIndex``\s*\)",
        flags=re.IGNORECASE,
    )
    assert pattern.search(source), (
        "Expected the v0.23.0 whatsnew entry for DataFrame.append to include an explicit "
        "categorical example, e.g. '(e.g. if both are ``CategoricalIndex``)'. This ensures "
        "the release note documents the concrete case the change addresses."
    )