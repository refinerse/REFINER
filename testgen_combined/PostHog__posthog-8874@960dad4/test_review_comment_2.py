import re


def test_clickhouse_trends_uses_typing_cast_for_threaded_results_and_parse_functions():
    """
    Review comment requested using typing.cast().

    We can't import this module in the execution environment (Django settings abort),
    so we assert at source level that the implementation uses `cast(...)` in the
    threaded parallel path, specifically:
      - imports `cast` from typing
      - uses `cast` to index into `parse_functions`
      - uses `cast` when flattening `result` items
    """
    source = open("/workspace/ee/clickhouse/queries/trends/clickhouse_trends.py").read()

    assert (
        "from typing import" in source and "cast" in source
    ), "Expected `cast` to be imported from typing in clickhouse_trends.py"

    assert re.search(r"\bcast\s*\(", source), "Expected usage of `cast(...)` in clickhouse_trends.py"

    assert re.search(
        r"cast\s*\(\s*List\s*\[\s*Callable\s*\]\s*,\s*parse_functions\s*\)\s*\[\s*entity\.index\s*\]",
        source,
    ), (
        "Expected `parse_functions` to be indexed via `cast(List[Callable], parse_functions)[entity.index]` "
        "to satisfy the review comment."
    )

    assert re.search(
        r"for\s+flat\s+in\s+cast\s*\(\s*List\s*\[\s*Dict\s*\[\s*str\s*,\s*Any\s*\]\s*\]\s*,\s*item\s*\)\s*:",
        source,
    ), (
        "Expected flattening loop to iterate with `for flat in cast(List[Dict[str, Any]], item):` "
        "instead of `if item is not None` checks, demonstrating use of `cast()`."
    )