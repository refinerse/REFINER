import pytest

import sky
from sky import clouds
import sky.backends.cloud_vm_ray_backend as backend_mod


def test_nodes_launching_progress_timeout_is_cloud_specific_and_lambda_only_increased():
    """Ensure timeout is not globally increased for all clouds.

    Review intent: only Lambda should have a higher timeout; other clouds should
    keep the previous value (90s).
    """
    timeout = getattr(backend_mod, "_NODES_LAUNCHING_PROGRESS_TIMEOUT")

    assert isinstance(
        timeout, dict
    ), (
        "_NODES_LAUNCHING_PROGRESS_TIMEOUT must be a dict keyed by cloud types "
        "so only Lambda's timeout can be increased without affecting others."
    )

    expected_cloud_keys = {
        clouds.AWS,
        clouds.Azure,
        clouds.GCP,
        clouds.Lambda,
        clouds.Local,
    }
    assert expected_cloud_keys.issubset(set(timeout.keys())), (
        "Timeout dict must include entries for AWS/Azure/GCP/Lambda/Local so "
        "non-Lambda clouds are not affected by a higher timeout."
    )

    assert timeout[clouds.Lambda] > timeout[clouds.AWS], (
        "Lambda should have a higher nodes-launching progress timeout than AWS "
        "(and thus other non-Lambda clouds)."
    )

    assert timeout[clouds.AWS] == 90, "AWS timeout should remain 90 seconds."
    assert timeout[clouds.Azure] == 90, "Azure timeout should remain 90 seconds."
    assert timeout[clouds.GCP] == 90, "GCP timeout should remain 90 seconds."
    assert timeout[clouds.Local] == 90, "Local timeout should remain 90 seconds."
    assert timeout[clouds.Lambda] == 120, "Lambda timeout should be increased to 120 seconds."