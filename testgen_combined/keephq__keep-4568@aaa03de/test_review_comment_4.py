import pytest

from keep.api.models.alert import BatchEnrichAlertRequestBody


def test_batch_enrich_request_body_does_not_expose_pagination_fields():
    """
    Structural API test:
    The batch enrichment request body should NOT expose pagination parameters
    (limit/offset) as part of the public API. Those should be hardcoded where used.
    """
    model_fields = set(getattr(BatchEnrichAlertRequestBody, "__fields__", {}).keys())

    assert "limit" not in model_fields, (
        "BatchEnrichAlertRequestBody must not expose 'limit' as a request field; "
        "pagination should be hardcoded at the usage site."
    )
    assert "offset" not in model_fields, (
        "BatchEnrichAlertRequestBody must not expose 'offset' as a request field; "
        "pagination should be hardcoded at the usage site."
    )