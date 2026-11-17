import re


def test_get_inner_event_query_does_not_use_mutable_default_entities_list():
    """
    Regression test for Python mutable default args:

    _get_inner_event_query must not define `entities` with a list default (entities=[]),
    because that list is shared across calls. It should use `entities=None` instead.
    """
    source = open("/workspace/ee/clickhouse/queries/funnels/base.py").read()

    # Ensure the function exists so the test is meaningful.
    assert (
        "def _get_inner_event_query" in source
    ), "Expected ClickhouseFunnelBase._get_inner_event_query to exist in /workspace/ee/clickhouse/queries/funnels/base.py"

    # Fail if the known-bad signature exists (before code).
    assert (
        "def _get_inner_event_query(self, entities=[], entity_name=" not in source
    ), (
        "Mutable default argument detected: `_get_inner_event_query(self, entities=[], ...)`.\n"
        "This list would be shared across calls; use `entities=None` instead."
    )

    # Require the fixed signature (after code).
    assert re.search(
        r"def _get_inner_event_query\(\s*self\s*,\s*entities\s*=\s*None\s*,\s*entity_name\s*=\s*[\"']events[\"']\s*\)\s*->\s*str\s*:",
        source,
    ), (
        "Expected `_get_inner_event_query` signature to use `entities=None` and default "
        "`entity_name='events'`, e.g.:\n"
        "    def _get_inner_event_query(self, entities=None, entity_name=\"events\") -> str:"
    )