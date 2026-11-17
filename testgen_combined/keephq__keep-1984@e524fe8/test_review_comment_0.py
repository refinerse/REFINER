import inspect
from uuid import UUID

import keep.api.routes.topology as topology


def test_update_application_expects_uuid_application_id_param_type():
    """
    Review comment implies the PUT /applications/{application_id} endpoint should
    treat application_id as a UUID (not a plain str). This test asserts the
    runtime function signature reflects that.

    Before: application_id annotated as str -> should FAIL.
    After: application_id annotated as uuid.UUID -> should PASS.
    """
    sig = inspect.signature(topology.update_application)
    assert "application_id" in sig.parameters, "update_application must accept an application_id parameter"

    annotation = sig.parameters["application_id"].annotation
    assert (
        annotation is UUID
    ), f"update_application.application_id must be annotated as uuid.UUID, got {annotation!r}"