import re


def test_whatsnew_0210_rolling_quantile_entry_references_funcs_and_issues():
    source = open("/workspace/doc/source/whatsnew/v0.21.0.txt", encoding="utf-8").read()

    # The review requested:
    # 1) use :func:`Series.quantile()` and :func:`DataFrame.quantile()` (not plain text)
    # 2) add issue numbers #9413 and #16211
    #
    # We assert the exact bullet line exists to avoid ambiguous matches elsewhere in the file.
    pattern = re.compile(
        r"- Bug in ``\.rolling\.quantile\(\)`` which incorrectly used different defaults than "
        r":func:`Series\.quantile\(\)` and :func:`DataFrame\.quantile\(\)` "
        r"\(:issue:`9413`, :issue:`16211`\)"
    )

    assert pattern.search(source), (
        "Expected v0.21.0 whatsnew entry for rolling.quantile to reference "
        ":func:`Series.quantile()` and :func:`DataFrame.quantile()` and include issue links "
        "(:issue:`9413`, :issue:`16211`). The required bullet line was not found."
    )