import pytest
from fastapi import HTTPException

import keep.api.routes.topology as topology


class _AuthEntity:
    def __init__(self, tenant_id: str = "t1"):
        self.tenant_id = tenant_id


def test_get_applications_maps_parse_exception_to_400_not_generic_500():
    """
    Review intent: avoid catching all exceptions generically; expected exceptions
    should be handled explicitly.

    Behavior check:
    - After fix: ApplicationParseException should be translated to HTTP 400.
    - Before fix: generic Exception handler returns HTTP 500 for the same failure.
    """
    # Ensure the custom exception exists on the module in the "after" version.
    # In the "before" version, it won't exist; in that case we raise a generic
    # Exception to trigger the old broad handler.
    parse_exc_cls = getattr(topology, "ApplicationParseException", None)

    def provoke_failure(*args, **kwargs):
        if parse_exc_cls is None:
            raise Exception("parse error")
        raise parse_exc_cls("parse error")

    # Patch by assignment (no unittest.mock) so we exercise the route function's
    # exception handling behavior.
    original = topology.TopologiesService.get_applications_by_tenant_id
    topology.TopologiesService.get_applications_by_tenant_id = provoke_failure
    try:
        with pytest.raises(HTTPException) as excinfo:
            topology.get_applications(authenticated_entity=_AuthEntity(), session=None)

        assert (
            excinfo.value.status_code == 400
        ), f"Expected parse errors to be mapped to HTTP 400, got {excinfo.value.status_code} instead."
        assert (
            "parse error" in str(excinfo.value.detail)
        ), "Expected the HTTPException detail to include the underlying parse error message."
    finally:
        topology.TopologiesService.get_applications_by_tenant_id = original