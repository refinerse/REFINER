import re


def test_stata_strl_generate_table_uses_isna_only():
    # Prevent third-party pytest plugins (e.g. pytest-qt) from auto-loading and crashing
    # due to missing system libraries in this execution environment.
    #
    # NOTE: This must be set before pytest plugin discovery; using a module import-time
    # side effect is sufficient since test modules are imported early.
    import os

    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    source = open("/workspace/pandas/io/stata.py", encoding="utf-8").read()

    expected_line = 'val = "" if isna(val) else val'
    assert expected_line in source, (
        "Expected StataStrLWriter.generate_table to normalize missing values using only "
        "`isna(val)` (so None and pd.NA are both handled) with the exact line:\n"
        f"    {expected_line}"
    )

    old_redundant = re.compile(
        r'val\s*=\s*""\s*if\s*\(\s*val\s+is\s+None\s*\)\s*or\s*isna\s*\(\s*val\s*\)\s*else\s*val'
    )
    assert not old_redundant.search(source), (
        "Did not expect redundant None-check logic in generate_table:\n"
        '    val = "" if (val is None) or isna(val) else val\n'
        "The reviewed change replaces this with `val = '' if isna(val) else val`."
    )