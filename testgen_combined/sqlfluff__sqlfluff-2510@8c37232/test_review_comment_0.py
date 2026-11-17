import importlib

import src.sqlfluff.dialects.dialect_tsql  # noqa: F401


def test_tsql_dialect_comment_typo_fixed():
    """Verify the review change: comment typo 'fucnctions' -> 'functions'.

    This is a runtime-observable change only via source inspection.
    """
    path = "/workspace/src/sqlfluff/dialects/dialect_tsql.py"
    source = open(path, "r", encoding="utf-8").read()

    assert (
        "# Treat functions which take date parts separately" in source
    ), (
        "Expected the comment text to be corrected to "
        "'# Treat functions which take date parts separately' in "
        f"{path}, but it was not found."
    )

    assert (
        "# Treat fucnctions which take date parts separately" not in source
    ), (
        "Expected the old misspelled comment "
        "'# Treat fucnctions which take date parts separately' to be removed "
        f"from {path}, but it is still present."
    )