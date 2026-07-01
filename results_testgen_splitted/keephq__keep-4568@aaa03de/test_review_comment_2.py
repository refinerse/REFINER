import pytest

import keep.api.routes.alerts as alerts_module


def test_batch_enrich_cel_does_not_override_querydto_defaults_with_request_limit_offset(
    monkeypatch,
):
    """
    Correct behavior (after): when CEL is provided, the backend must call:
        query_last_alerts(..., query=QueryDto(cel=enrich_data.cel))
    i.e. it must NOT explicitly pass enrich_data.limit/offset into QueryDto construction.

    We verify this by making enrich_data.limit/offset intentionally different from QueryDto defaults.
    - Before: QueryDto(limit=enrich_data.limit, offset=enrich_data.offset) -> differs from defaults -> FAIL
    - After:  QueryDto(cel=...) only -> uses defaults -> PASS
    """

    class DummyAuthenticatedEntity:
        tenant_id = "t1"
        email = "user@example.com"

    class DummyAlert:
        def __init__(self, fingerprint: str):
            self.fingerprint = fingerprint

    captured = {"query_dto": None}

    def fake_query_last_alerts(*, tenant_id, query):
        captured["query_dto"] = query
        return [DummyAlert("fp-1")], 1

    class DummyEnrichmentsBl:
        def __init__(self, tenant_id, db=None):
            self.tenant_id = tenant_id
            self.db = db

        def get_enrichment_metadata(self, enrichments, authenticated_entity):
            return "ACTION", "desc", False, False

        def batch_enrich(self, **kwargs):
            return None

    def fake_get_last_alerts_by_fingerprints(tenant_id, fingerprints, session=None):
        class DummyLastAlert:
            def __init__(self, alert_id):
                self.alert_id = alert_id

        return [DummyLastAlert("a1")]

    def fake_get_alerts_by_ids(tenant_id, alert_ids, session=None):
        return []

    def fake_convert_db_alerts_to_dto_alerts(*args, **kwargs):
        return []

    def fake_get_pusher_client():
        return None

    class DummyElasticClient:
        def __init__(self, tenant_id):
            self.tenant_id = tenant_id

        def index_alerts(self, alerts):
            return None

    monkeypatch.setattr(alerts_module, "query_last_alerts", fake_query_last_alerts)
    monkeypatch.setattr(alerts_module, "EnrichmentsBl", DummyEnrichmentsBl)
    monkeypatch.setattr(
        alerts_module,
        "get_last_alerts_by_fingerprints",
        fake_get_last_alerts_by_fingerprints,
    )
    monkeypatch.setattr(alerts_module, "get_alerts_by_ids", fake_get_alerts_by_ids)
    monkeypatch.setattr(
        alerts_module,
        "convert_db_alerts_to_dto_alerts",
        fake_convert_db_alerts_to_dto_alerts,
    )
    monkeypatch.setattr(alerts_module, "get_pusher_client", fake_get_pusher_client)
    monkeypatch.setattr(alerts_module, "ElasticClient", DummyElasticClient)

    # Intentionally set limit/offset to values that differ from QueryDto defaults
    default_query = alerts_module.QueryDto()
    non_default_limit = default_query.limit + 7
    non_default_offset = default_query.offset + 3

    class DummyBatchEnrichData:
        def __init__(self):
            self.enrichments = {}
            self.fingerprints = None
            self.cel = "name.contains('CPU')"
            self.limit = non_default_limit
            self.offset = non_default_offset

    enrich_data = DummyBatchEnrichData()

    result = alerts_module.batch_enrich_alerts(
        enrich_data=enrich_data,
        authenticated_entity=DummyAuthenticatedEntity(),
        dispose_on_new_alert=False,
        session=None,
    )
    assert result == {"status": "ok"}, "Expected batch_enrich_alerts to return {'status': 'ok'}"

    query_dto = captured["query_dto"]
    assert (
        query_dto is not None
    ), "Expected batch_enrich_alerts to call query_last_alerts when CEL is provided"
    assert (
        query_dto.cel == enrich_data.cel
    ), "QueryDto passed to query_last_alerts must contain the provided CEL expression"

    assert query_dto.limit == default_query.limit, (
        "When enriching by CEL, the selection query should NOT override QueryDto.limit using request-provided "
        "BatchEnrichAlertRequestBody.limit; it should keep QueryDto defaults."
    )
    assert query_dto.offset == default_query.offset, (
        "When enriching by CEL, the selection query should NOT override QueryDto.offset using request-provided "
        "BatchEnrichAlertRequestBody.offset; it should keep QueryDto defaults."
    )