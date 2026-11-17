import pytest


def test_topologies_service_defines_domain_exceptions_not_fastapi_http_exception():
    """
    Structural change: move away from FastAPI-layer HTTPException usage in the service layer
    and introduce domain exceptions (TopologyException and specific subclasses).

    This should FAIL on the "before" code because:
      - TopologyException hierarchy does not exist
      - update_application_by_id raises fastapi.HTTPException

    This should PASS on the "after" code because:
      - TopologyException hierarchy exists
      - update_application_by_id does not use HTTPException
    """
    import keep.topologies.topologies_service as ts

    # After code introduces these domain exceptions; before code doesn't.
    assert hasattr(
        ts, "TopologyException"
    ), "Expected TopologyException to exist (service-layer domain exceptions introduced)."
    assert hasattr(
        ts, "ApplicationNotFoundException"
    ), "Expected ApplicationNotFoundException to exist (replacing HTTPException for not-found)."

    # Ensure service layer no longer depends on FastAPI HTTPException (structural separation).
    source = open("/workspace/keep/topologies/topologies_service.py", "r", encoding="utf-8").read()
    assert (
        "from fastapi import HTTPException" not in source and "HTTPException" not in source
    ), "TopologiesService should not import/use fastapi.HTTPException; it should raise domain exceptions instead."