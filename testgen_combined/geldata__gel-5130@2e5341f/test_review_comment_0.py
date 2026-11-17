import re


def test_selectquery_where_orderby_not_wrapped_in_disallow_dml_context():
    """
    The review feedback requested that DML-disallowing context should be applied
    in clauses compilation generally (so it affects UPDATE/DELETE where too),
    rather than wrapping only SELECT's where/orderby in stmt.compile_SelectQuery.

    This test asserts that compile_SelectQuery does *not* introduce a NEW context
    that sets disallow_dml=True around WHERE/ORDER BY compilation.
    """
    source = open("/workspace/edb/edgeql/compiler/stmt.py", "r", encoding="utf-8").read()

    # Sanity check: make sure we are looking at the expected function.
    assert "def compile_SelectQuery(" in source, "Expected compile_SelectQuery() to exist in stmt.py"

    # This is the "before" pattern: a NEW context used only to set disallow_dml
    # around SELECT's where/orderby clause compilation.
    forbidden_pattern = re.compile(
        r"with\s+sctx\.new\(\s*context\.ContextSwitchMode\.NEW\s*\)\s+as\s+\w+\s*:\s*\n"
        r"\s*\w+\.disallow_dml\s*=\s*True",
        re.MULTILINE,
    )

    assert not forbidden_pattern.search(source), (
        "compile_SelectQuery() should not create a NEW context solely to set "
        "disallow_dml=True around WHERE/ORDER BY compilation; this restriction "
        "belongs in clauses compilation so it applies to UPDATE/DELETE where too."
    )