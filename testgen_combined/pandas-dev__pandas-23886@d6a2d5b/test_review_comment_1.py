import pandas as pd
from pandas.core.generic import _shared_docs


def test_shared_docs_melt_docstring_does_not_start_with_quotes():
    """
    The shared docstring for melt should not start with quotes.

    This matches the review request to "simply remove the quotes" and ensures
    docstring validation tools don't see a leading quote character.
    """
    doc = _shared_docs["melt"]

    assert isinstance(doc, str) and doc, (
        "Expected pandas.core.generic._shared_docs['melt'] to be a non-empty string"
    )

    stripped = doc.lstrip()
    assert not stripped.startswith(("'", '"')), (
        "Expected pandas.core.generic._shared_docs['melt'] to not start with a quote "
        "after leading whitespace is stripped; quotes should be removed (e.g. start with "
        "'Unpivots ...' rather than \"'Unpivots' ...\"). "
        f"Got leading snippet: {stripped[:30]!r}"
    )

    assert stripped.startswith("Unpivots"), (
        "Expected melt shared docstring to start with 'Unpivots' once quotes are removed; "
        f"got leading snippet: {stripped[:30]!r}"
    )