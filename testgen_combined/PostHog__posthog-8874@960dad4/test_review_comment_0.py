import re


def test_run_parallel_does_not_recompute_sql_parse_function_after_threads():
    """
    Regression test for threading behavior in ClickhouseTrends._run_parallel.

    The fixed implementation caches parse_functions during SQL generation, instead of
    calling _get_sql_for_entity again after threads have executed. This avoids attempting
    to (re)generate SQL/params (and potentially reconnect) outside the main flow.

    We can't import the module in this environment, so we assert on source patterns.
    """
    source = open("/workspace/ee/clickhouse/queries/trends/clickhouse_trends.py").read()

    # Ensure the helper array exists (added by the fix)
    assert (
        "parse_functions" in source
    ), "Expected _run_parallel to cache parse functions in a parse_functions list to avoid recomputing SQL/parsers after threading."

    # The fixed code stores parse_function during the thread setup loop.
    assert (
        "parse_functions[entity.index] = parse_function" in source
    ), "Expected _run_parallel to store parse_function per entity index during thread setup."

    # The fixed code should NOT call _get_sql_for_entity again in the parsing phase.
    assert (
        "_, _, parse_function = self._get_sql_for_entity" not in source
    ), "Expected _run_parallel to avoid calling _get_sql_for_entity again after threads complete; it should use cached parse_functions instead."

    # The fixed code should use the cached parse_functions to parse results.
    assert re.search(
        r"parse_functions\)\s*\[\s*entity\.index\s*\]\s*\(\s*result\[\s*entity\.index\s*\]\s*\)",
        source,
        flags=re.MULTILINE,
    ), "Expected _run_parallel to parse thread results using cached parse_functions[entity.index](result[entity.index])."