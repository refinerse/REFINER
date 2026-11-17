from keep.api.models.alert import BatchEnrichAlertRequestBody


def test_batch_enrich_request_body_no_default_pagination_fields_present():
    """
    Review intent: BatchEnrichAlertRequestBody should NOT include pagination fields
    (limit/offset). They were present in the buggy version with defaults.

    This test checks the runtime shape of the Pydantic model instance.
    - Before (buggy): model has limit=1000 and offset=0 fields -> assertion fails.
    - After (correct): those fields do not exist -> assertion passes.
    """
    obj = BatchEnrichAlertRequestBody(enrichments={"owner": "team-a"})

    dumped = obj.dict()
    assert "limit" not in dumped and "offset" not in dumped, (
        "BatchEnrichAlertRequestBody should not define/serialize pagination fields "
        "'limit' and 'offset'. Their presence indicates the buggy version where "
        "they were added with defaults."
    )