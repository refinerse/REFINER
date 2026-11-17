import re


def test_funnel_event_query_uses_or_fallback_for_entities_to_use():
    source = open("/workspace/ee/clickhouse/queries/funnels/funnel_event_query.py").read()

    # Style expectation from review: use `entities or self._filter.entities`
    # instead of an if/len check or mutable default args patterns.
    assert (
        "entities_to_use = entities or self._filter.entities" in source
    ), (
        "Expected FunnelEventQuery._get_entity_query to use the concise fallback pattern "
        "`entities_to_use = entities or self._filter.entities` (per style review), "
        "but it was not found in /workspace/ee/clickhouse/queries/funnels/funnel_event_query.py."
    )

    # Ensure the old verbose pattern isn't present (guards against regressions).
    old_pattern = re.compile(
        r"entities_to_use\s*=\s*self\._filter\.entities\s*\n\s*if\s+len\(entities\)\s*>\s*0:\s*\n\s*entities_to_use\s*=\s*entities",
        re.MULTILINE,
    )
    assert not old_pattern.search(source), (
        "Found the old verbose entities selection pattern:\n"
        "    entities_to_use = self._filter.entities\n"
        "    if len(entities) > 0:\n"
        "        entities_to_use = entities\n"
        "Expected it to be replaced with `entities_to_use = entities or self._filter.entities`."
    )