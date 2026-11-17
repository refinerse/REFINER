import re


def test_get_inner_event_query_uses_none_default_and_or_fallback():
    source = open("/workspace/ee/clickhouse/queries/funnels/base.py").read()

    # Verify the style change: avoid mutable default arg `entities=[]` and prefer
    # `entities=None` with `entities_to_use = entities or self._filter.entities`.
    #
    # This should FAIL on the "before" code which uses:
    #   def _get_inner_event_query(self, entities=[], ...)
    #   entities_to_use = self._filter.entities
    #   if entities: entities_to_use = entities
    #
    # And PASS on the "after" code which uses:
    #   def _get_inner_event_query(self, entities=None, ...)
    #   entities_to_use = entities or self._filter.entities

    assert (
        "def _get_inner_event_query(self, entities=None, entity_name=" in source
    ), "Expected _get_inner_event_query to default entities to None (not a mutable [])."

    assert (
        "entities_to_use = entities or self._filter.entities" in source
    ), "Expected entities_to_use to be assigned via `entities or self._filter.entities`."

    # Ensure the old pattern is not present (guards against partial/incorrect refactor).
    assert not re.search(
        r"def _get_inner_event_query\(\s*self\s*,\s*entities\s*=\s*\[\s*\]\s*,\s*entity_name\s*=",
        source,
    ), "Did not expect _get_inner_event_query to have a mutable default `entities=[]`."