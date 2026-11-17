import re


def test_run_parallel_does_not_recompute_sql_parse_function_per_entity():
    """
    Regression test for review comment:
    In _run_parallel, we should not call _get_sql_for_entity twice per entity (once for SQL/params and again for parse_function).
    Instead, parse functions should be captured during thread setup and reused after joining threads.

    This test is source-based because importing the module fails in this environment.
    """
    source = open("/workspace/ee/clickhouse/queries/trends/clickhouse_trends.py").read()

    # Ensure _run_parallel exists (sanity check so test is meaningful).
    assert "def _run_parallel" in source, "Expected ClickhouseTrends._run_parallel to exist in clickhouse_trends.py"

    # Key behavior check:
    # BEFORE: there is a second call pattern: "_, _, parse_function = self._get_sql_for_entity(...)" in the parse loop.
    # AFTER: parse_functions are stored and later used (with cast(...) indexing).
    forbidden_second_call_pattern = r"_,\s*_,\s*parse_function\s*=\s*self\._get_sql_for_entity\("
    assert (
        re.search(forbidden_second_call_pattern, source) is None
    ), "Expected _run_parallel to avoid recomputing parse_function by calling _get_sql_for_entity a second time."

    # Also assert the new mechanism exists to prevent false positives:
    assert (
        "parse_functions" in source
    ), "Expected _run_parallel to store parse functions (e.g. parse_functions list) rather than recomputing them."

    # Ensure parse_functions are actually used to parse results
    assert (
        "parse_functions)[entity.index]" in source or "parse_functions[entity.index]" in source
    ), "Expected _run_parallel to parse results using the stored parse function for each entity index."