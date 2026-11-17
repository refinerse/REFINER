import re

from sklearn.feature_extraction.text import TfidfVectorizer


def test_tfidfvectorizer_doc_does_not_list_countvectorizer_as_parameter():
    """
    Regression test for a documentation issue:

    The TfidfVectorizer docstring must not list "CountVectorizer" (or
    "TfidfTransformer") as if it were an __init__ parameter in the
    "Parameters" section. Those belong in "See also" / narrative text.
    """
    doc = TfidfVectorizer.__doc__
    assert doc is not None and "Parameters" in doc, "TfidfVectorizer docstring should exist and document Parameters."

    # Extract the "Parameters" block up to (but not including) "Attributes".
    m = re.search(r"\n\s*Parameters\s*\n\s*-+\s*\n(.*?)\n\s*Attributes\s*\n\s*-+\s*\n", doc, flags=re.S)
    assert m is not None, (
        "Expected to find a 'Parameters' section followed by an 'Attributes' section "
        "in TfidfVectorizer.__doc__."
    )
    params_block = m.group(1)

    # In the buggy version, these appear as parameter entries like:
    # "CountVectorizer : sparse matrix, (n_samples, n_features)"
    assert "CountVectorizer :" not in params_block, (
        "TfidfVectorizer.__doc__ incorrectly lists 'CountVectorizer' as a parameter "
        "in the 'Parameters' section. It should be described elsewhere (e.g. in "
        "'See also' or narrative text)."
    )
    assert "TfidfTransformer :" not in params_block, (
        "TfidfVectorizer.__doc__ incorrectly lists 'TfidfTransformer' as a parameter "
        "in the 'Parameters' section. It should be described elsewhere (e.g. in "
        "'See also' or narrative text)."
    )