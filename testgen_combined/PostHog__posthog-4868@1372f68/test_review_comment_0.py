import re

import pytest


def test_funnel_event_query_uses_none_default_for_entities_argument():
    source = open("/workspace/ee/clickhouse/queries/funnels/funnel_event_query.py").read()

    # Style requirement from review: avoid mutable default argument `entities=[]`
    # and use `entities=None` instead.
    assert "def get_query(self, entities=[], entity_name=" not in source, (
        "FunnelEventQuery.get_query should not use a mutable default `entities=[]`. "
        "Use `entities=None` instead."
    )

    # Also ensure the intended signature exists.
    assert re.search(
        r"def\s+get_query\(\s*self\s*,\s*entities\s*=\s*None\s*,\s*entity_name\s*=\s*[\"']events[\"']\s*\)\s*->",
        source,
    ), (
        "Expected FunnelEventQuery.get_query signature to be "
        "`def get_query(self, entities=None, entity_name=\"events\") -> ...`."
    )

    # Same style fix should apply to the helper too.
    assert "def _get_entity_query(self, entities=[], entity_name=" not in source, (
        "FunnelEventQuery._get_entity_query should not use a mutable default `entities=[]`. "
        "Use `entities=None` instead."
    )
    assert re.search(
        r"def\s+_get_entity_query\(\s*self\s*,\s*entities\s*=\s*None\s*,\s*entity_name\s*=\s*[\"']events[\"']\s*\)\s*->",
        source,
    ), (
        "Expected FunnelEventQuery._get_entity_query signature to be "
        "`def _get_entity_query(self, entities=None, entity_name=\"events\") -> ...`."
    )