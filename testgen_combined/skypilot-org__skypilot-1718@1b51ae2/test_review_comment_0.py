import importlib

import pytest


def test_lambda_node_provider_internal_constants_prefixed_with_underscore():
    """Review comment asks to prefix internal module-level variables with `_`.

    This test ensures the public (non-underscored) names are not exposed, and
    the underscored versions exist.
    """
    mod = importlib.import_module("sky.skylet.providers.lambda_cloud.node_provider")

    # These should be internal/private constants and not exposed as public names.
    assert not hasattr(
        mod, "TAG_PATH_PREFIX"
    ), "TAG_PATH_PREFIX should be renamed to _TAG_PATH_PREFIX (internal constant)."
    assert not hasattr(
        mod, "REMOTE_RAY_SSH_KEY"
    ), "REMOTE_RAY_SSH_KEY should be renamed to _REMOTE_RAY_SSH_KEY (internal constant)."
    assert not hasattr(
        mod, "GET_INTERNAL_IP_CMD"
    ), "GET_INTERNAL_IP_CMD should be renamed to _GET_INTERNAL_IP_CMD (internal constant)."

    # The underscored internal constants should exist.
    assert hasattr(
        mod, "_TAG_PATH_PREFIX"
    ), "Expected internal constant _TAG_PATH_PREFIX to exist."
    assert hasattr(
        mod, "_REMOTE_RAY_SSH_KEY"
    ), "Expected internal constant _REMOTE_RAY_SSH_KEY to exist."
    assert hasattr(
        mod, "_GET_INTERNAL_IP_CMD"
    ), "Expected internal constant _GET_INTERNAL_IP_CMD to exist."