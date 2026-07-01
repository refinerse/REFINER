import inspect

import src.sqlfluff.dialects.dialect_bigquery as bigquery_mod


def test_bigquery_functionsegment_comment_spelling_functions():
    """Ensure the FunctionSegment comment uses correct spelling 'functions'.

    This is a style-only change and has no runtime behavior impact, so we
    verify it by source inspection of the FunctionSegment class definition.
    """
    src = inspect.getsource(bigquery_mod.FunctionSegment)
    assert (
        "# Treat functions which take date parts separately" in src
    ), (
        "Expected FunctionSegment source to contain the corrected comment "
        "'# Treat functions which take date parts separately'. This should fail if the "
        "comment still contains the typo 'fucnctions'."
    )