import re


def test_mongodb_provider_does_not_use_db_eval_and_uses_command_api():
    source = open(
        "/workspace/keep/providers/mongodb_provider/mongodb_provider.py", "r", encoding="utf-8"
    ).read()

    # Eval (db.eval / database.eval) is removed/unsupported in newer MongoDB versions.
    assert ".eval(" not in source, (
        "MongoDB provider should not use database.eval()/db.eval(), which is removed/"
        "unsupported in newer MongoDB versions. Expected code to use database.command(...) instead."
    )

    # The updated implementation should use the supported command API.
    assert re.search(r"\bdatabase\.command\s*\(", source), (
        "MongoDB provider should use database.command(...) to execute queries "
        "instead of database.eval(...)."
    )