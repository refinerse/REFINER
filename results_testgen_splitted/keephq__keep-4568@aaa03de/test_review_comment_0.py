import pytest

import keep.api.routes.alerts as alerts_module


def test_batch_enrich_alerts_cel_does_not_forward_pagination_to_query_last_alerts():
    """
    The CEL-path in batch_enrich_alerts should NOT pass offset/limit to QueryDto when
    calling query_last_alerts. The reviewed change removed `offset=...` (and `limit=...`)
    from QueryDto construction for the CEL query.

    This test verifies that query_last_alerts is invoked with QueryDto that has
    default pagination values (offset=0, limit=1000), regardless of enrich_data.offset/limit.
    """

    # --- Arrange: patch module globals without unittest.mock (keep test self-contained) ---
    called = {}

    original_query_last_alerts = alerts_module.query_last_alerts
    original_query_dto_cls = alerts_module.QueryDto

    def fake_query_last_alerts(*, tenant_id, query):
        called["tenant_id"] = tenant_id
        called["query"] = query
        # Return empty results to stop execution early and avoid DB / enrichment side effects
        return [], 0

    alerts_module.query_last_alerts = fake_query_last_alerts

    class FakeAuthenticatedEntity:
        tenant_id = "t1"
        email = "user@example.com"

    class FakeBatchEnrichAlertRequestBody:
        # Provide both cel and non-default pagination; cel branch should ignore them
        cel = "name.contains('CPU')"
        fingerprints = None
        enrichments = {}
        limit = 7
        offset = 13

    try:
        # --- Act ---
        result = alerts_module.batch_enrich_alerts(
            enrich_data=FakeBatchEnrichAlertRequestBody(),
            authenticated_entity=FakeAuthenticatedEntity(),
            dispose_on_new_alert=False,
            session=None,
        )

        # --- Assert (1): ensure we hit the CEL branch and returned early as intended ---
        assert result == {
            "status": "ok",
            "message": "No alerts matched the query",
        }, "Expected early OK response when CEL query matches no alerts (fake_query_last_alerts returns empty)."

        # --- Assert (2): core behavior change ---
        assert "query" in called, "Expected query_last_alerts to be called in the CEL path."
        q = called["query"]
        assert isinstance(
            q, original_query_dto_cls
        ), "Expected query_last_alerts to receive a QueryDto instance."

        assert (
            q.offset == 0
        ), f"Expected CEL QueryDto offset to remain default (0), not be forwarded from enrich_data.offset; got {q.offset}."
        assert (
            q.limit == 1000
        ), f"Expected CEL QueryDto limit to remain default (1000), not be forwarded from enrich_data.limit; got {q.limit}."

    finally:
        # Restore patched symbol
        alerts_module.query_last_alerts = original_query_last_alerts