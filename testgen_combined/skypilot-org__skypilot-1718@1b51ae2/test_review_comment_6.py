import pytest

import sky.skylet.providers.lambda_cloud.node_provider as node_provider
from sky.skylet.providers.lambda_cloud import lambda_utils


def test_get_internal_ip_failure_raises_informative_error(monkeypatch):
    """Ensure failing SSH command uses handle_returncode (not assert).

    Before fix: _get_internal_ip() used `assert out[0] == 0`, raising
      AssertionError (unhelpful, may be optimized away).
    After fix: uses subprocess_utils.handle_returncode(), raising a proper
      exception with the provided message.
    """
    # Avoid any real Lambda Cloud / filesystem interactions.
    monkeypatch.setattr(
        node_provider.lambda_utils,
        "LambdaCloudClient",
        lambda: type(
            "Client",
            (),
            {"list_instances": lambda self: [{"id": "vm-1", "status": "active", "ip": "1.2.3.4", "name": "c-head"}]},
        )(),
    )

    class _FakeMetadata:
        def __init__(self, *args, **kwargs):
            self._store = {}

        def refresh(self, ids):
            return None

        def exists(self, _id):
            # "before" code uses .exists(); returning True avoids writes via __setitem__.
            return True

        def __getitem__(self, _id):
            # Provide tags for filtering.
            return {"tags": {node_provider.TAG_RAY_CLUSTER_NAME: "c"}}

        # "after" code uses .get() / .set()
        def get(self, _id):
            return {"tags": {node_provider.TAG_RAY_CLUSTER_NAME: "c"}}

        def set(self, _id, val):
            self._store[_id] = val

    monkeypatch.setattr(node_provider.lambda_utils, "Metadata", _FakeMetadata)

    # Force SSH command to fail.
    class _FailingRunner:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, cmd, require_outputs=True, stream_logs=False):
            # Both versions call SSHCommandRunner.run(); before expects tuple-like
            # with rc at index 0, stdout at index 1. After unpacks rc, stdout, stderr.
            return (1, "stdout-from-failure\n", "stderr-from-failure\n")

    monkeypatch.setattr(node_provider.command_runner, "SSHCommandRunner", _FailingRunner)

    provider = node_provider.LambdaNodeProvider(provider_config={"region": "x"}, cluster_name="c")

    # Trigger _get_internal_ip via _get_filtered_nodes().
    with pytest.raises(Exception) as excinfo:
        provider._get_filtered_nodes({node_provider.TAG_RAY_CLUSTER_NAME: "c"})

    # The key behavior: should NOT be AssertionError; should be a real exception
    # raised through handle_returncode with an informative message.
    assert not isinstance(
        excinfo.value, AssertionError
    ), "Expected an informative exception via subprocess_utils.handle_returncode(), not AssertionError."

    assert (
        "Failed get obtain private IP from node" in str(excinfo.value)
    ), "Error message should include the handle_returncode() message for easier debugging."