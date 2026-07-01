import pytest

from sky.skylet.providers.lambda_cloud import lambda_utils


def test_get_filtered_nodes_raises_clear_error_when_ip_missing(monkeypatch):
    """_get_filtered_nodes should raise LambdaCloudError with a helpful message
    if Lambda Cloud returns an instance without an 'ip' field.

    Before fix: KeyError('ip') escapes from _extract_metadata().
    After fix: LambdaCloudError is raised with a clear message.
    """
    # Avoid needing real Lambda credentials during LambdaNodeProvider.__init__.
    class _DummyLambdaClient:
        def list_instances(self):
            return []

        def create_instances(self, *args, **kwargs):
            return ["vm-1"]

        def remove_instances(self, *args, **kwargs):
            return None

    monkeypatch.setattr(lambda_utils, "LambdaCloudClient", _DummyLambdaClient)

    from sky.skylet.providers.lambda_cloud.node_provider import LambdaNodeProvider

    provider = LambdaNodeProvider(provider_config={"region": "dummy"},
                                  cluster_name="testcluster")

    # Ensure metadata operations don't touch filesystem / require setup.
    class _InMemoryMetadata:
        def refresh(self, ids):
            return None

        def get(self, _id):
            return {"tags": {}}  # make tag matching work

        # Used by _guess_and_add_missing_tags (after code).
        def set(self, _id, value):
            return None

        # Used by _guess_and_add_missing_tags (before code).
        def exists(self, _id):
            return True

        # Used by _get_filtered_nodes (before code).
        def __getitem__(self, _id):
            return {"tags": {}}

    provider.metadata = _InMemoryMetadata()

    # Provide a VM lacking 'ip' to trigger the behavior under test.
    provider._list_instances_in_cluster = lambda: [{
        "id": "vm-1",
        "status": "active",
        "name": "testcluster-head",
        # no 'ip' key on purpose
    }]

    # Avoid any SSH / parallel execution: no nodes should reach that stage anyway
    # due to the missing 'ip', but keep this as a safeguard.
    from sky.utils import subprocess_utils as sky_subprocess_utils
    monkeypatch.setattr(sky_subprocess_utils, "run_in_parallel",
                        lambda fn, items: None)

    with pytest.raises(lambda_utils.LambdaCloudError) as excinfo:
        provider._get_filtered_nodes(tag_filters={})

    msg = str(excinfo.value)
    assert "ip address was not found" in msg, (
        "Expected LambdaCloudError with a clear message when 'ip' is missing "
        "from Lambda Cloud instance data. Got: %r" % msg
    )