import pytest

import sky.cli as cli


def test_launch_with_confirm_uses_core_autostop_for_up_interactive_nodes():
    """When attaching to an already-UP interactive node and the user requests
    autostop/autodown, CLI should use the programmatic API core.autostop(),
    not backend.set_autostop().

    This is validated by:
      - monkeypatching cli.core.autostop to record calls
      - using a backend object that would fail if set_autostop() is invoked
      - forcing cluster status to UP so _launch_with_confirm() won't call sky.launch()
    """
    # Record calls to core.autostop without using unittest.mock.
    calls = []

    def _recording_autostop(cluster: str, idle_minutes: int, down: bool):
        calls.append((cluster, idle_minutes, down))

    # Make sure we never reach sky.launch() in this scenario (UP interactive node).
    def _launch_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "sky.launch() should not be called when interactive node is already "
            "UP; CLI should only update autostop/autodown settings."
        )

    class _BackendThatMustNotBeUsedForAutostop:
        def set_autostop(self, *args, **kwargs):
            raise AssertionError(
                "backend.set_autostop() should not be used; expected "
                "cli.core.autostop() to be called instead."
            )

        def check_resources_fit_cluster(self, handle, task):
            # Not relevant for this test (we also patch _check_resources_match).
            return

    cluster_name = "my-up-node"

    # Patch dependencies on the imported cli module.
    cli.core.autostop = _recording_autostop
    cli.sky.launch = _launch_should_not_be_called
    cli._check_resources_match = lambda *a, **k: None  # avoid handle lookups

    # Force the cluster status to UP.
    def _refresh_status_handle(_cluster: str):
        return (cli.global_user_state.ClusterStatus.UP, None)

    cli.backend_utils.refresh_cluster_status_handle = _refresh_status_handle

    # Create a minimal dag/task that _launch_with_confirm expects.
    with cli.sky.Dag() as dag:
        task = cli.sky.Task("noop", run="echo noop")
        task.set_resources({cli.sky.Resources()})

    backend = _BackendThatMustNotBeUsedForAutostop()

    # Call the function under test: interactive node_type + UP status
    # should trigger core.autostop(), not backend.set_autostop().
    cli._launch_with_confirm(
        dag,
        backend,
        cluster_name,
        dryrun=False,
        detach_run=True,
        no_confirm=True,
        idle_minutes_to_autostop=15,
        down=False,
        retry_until_up=False,
        node_type="cpunode",
    )

    assert calls == [(cluster_name, 15, False)], (
        "Expected _launch_with_confirm() to update autostop settings for an "
        "already-UP interactive node by calling core.autostop(cluster, "
        "idle_minutes, down)."
    )