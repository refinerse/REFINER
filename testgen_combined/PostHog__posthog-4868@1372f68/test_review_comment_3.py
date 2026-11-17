import re


def test_funnel_event_query_avoids_mutable_default_for_entities_param():
    source = open("/workspace/ee/clickhouse/queries/funnels/funnel_event_query.py").read()

    # We specifically want to ensure the method signature was changed from
    # entities=[] (mutable default) to entities=None (safe default).
    # This is a style/API surface change observable from the source.
    assert "def _get_entity_query" in source, "Expected FunnelEventQuery._get_entity_query to exist in the source file."

    # Fail if the old (bad) signature is present
    assert (
        "def _get_entity_query(self, entities=[], entity_name=\"events\")" not in source
    ), (
        "FunnelEventQuery._get_entity_query should not use a mutable default "
        "argument (entities=[]). Expected entities=None."
    )

    # Pass only if the new (good) signature is present
    assert re.search(
        r"def _get_entity_query\(\s*self\s*,\s*entities\s*=\s*None\s*,\s*entity_name\s*=\s*[\"']events[\"']\s*\)",
        source,
    ), (
        "Expected FunnelEventQuery._get_entity_query to define entities=None and "
        'entity_name="events" in its signature.'
    )