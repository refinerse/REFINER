import pytest

import sky.skylet.providers.lambda_cloud.node_provider as node_provider


def test_get_internal_ip_calls_runner_run_with_rc_stdout_stderr_unpack(monkeypatch):
    """Regression test for the review fix.

    The fixed code must unpack runner.run(...) into exactly:
        rc, stdout, stderr
    The pre-fix code assigns the whole return tuple to a single variable `out`.

    We detect this by making runner.run() return a special object that:
      - is iterable into exactly 3 items (so unpacking works),
      - but raises if code tries to index it (out[0]/out[1]) or take len().
    This makes the "before" code fail while the "after" code succeeds.
    """

    # Avoid needing real Lambda credentials by bypassing client construction.
    class FakeLambdaClient:
        def list_instances(self):
            return []

    monkeypatch.setattr(node_provider.lambda_utils, "LambdaCloudClient",
                        lambda: FakeLambdaClient())

    class UnindexableTriple:
        def __iter__(self):
            # Allows: rc, stdout, stderr = runner.run(...)
            yield 0
            yield "10.0.0.123\n"
            yield ""

        def __getitem__(self, idx):
            raise AssertionError(
                "runner.run() return value was indexed (e.g., out[0]/out[1]). "
                "Expected code to unpack into rc, stdout, stderr."
            )

        def __len__(self):
            raise AssertionError(
                "runner.run() return value length was queried. "
                "Expected direct unpacking into rc, stdout, stderr."
            )

    class FakeRunner:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, *args, **kwargs):
            return UnindexableTriple()

    monkeypatch.setattr(node_provider.command_runner, "SSHCommandRunner", FakeRunner)

    # Execute sequentially to keep the failure deterministic and propagate exceptions.
    def fake_run_in_parallel(fn, items):
        for it in items:
            fn(it)

    monkeypatch.setattr(node_provider.subprocess_utils, "run_in_parallel",
                        fake_run_in_parallel)

    # Ensure returncode handling doesn't raise (rc==0).
    monkeypatch.setattr(node_provider.subprocess_utils, "handle_returncode",
                        lambda *a, **k: None)

    provider = node_provider.LambdaNodeProvider(provider_config={"region": "x"},
                                                cluster_name="c")

    provider._list_instances_in_cluster = lambda: [{
        "id": "vm-1",
        "name": "c-head",
        "status": "active",
        "ip": "203.0.113.10",
    }]

    # Make metadata deterministic: tags exist but irrelevant.
    provider.metadata.refresh = lambda ids: None
    provider._guess_and_add_missing_tags = lambda vms: None
    if hasattr(provider.metadata, "get"):
        provider.metadata.get = lambda _id: {"tags": {}}
    else:
        provider.metadata.__getitem__ = lambda _self, _id: {"tags": {}}

    nodes = provider._get_filtered_nodes(tag_filters={})

    assert nodes["vm-1"]["internal_ip"] == "10.0.0.123", (
        "Expected internal_ip to be set from stdout after unpacking "
        "(rc, stdout, stderr) returned by runner.run()."
    )