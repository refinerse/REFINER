import numpy as np
import pytest

import modin.engines.base.frame.partition_manager as pm


def test_wait_is_not_exposed_as_public_classmethod_anymore():
    """
    The review change moves waiting logic to a module-level decorator so it isn't
    exposed as a public API on BaseFrameManager.
    """
    assert not hasattr(
        pm.BaseFrameManager, "wait_computations"
    ), (
        "BaseFrameManager.wait_computations should not exist as a public classmethod; "
        "waiting logic must be implemented via a module-level decorator instead."
    )


def test_decorator_waits_for_partitions_only_in_benchmark_mode():
    """
    In benchmark mode, decorated functions should force synchronization by calling
    .wait() on every partition; outside benchmark mode, no waiting should occur.
    """

    class DummyBenchmarkMode:
        _value = False

        @classmethod
        def get(cls):
            return cls._value

    # Ensure the decorator exists (it was introduced by the change)
    assert hasattr(pm, "wait_computations_if_benchmark_mode"), (
        "Expected module-level decorator 'wait_computations_if_benchmark_mode' to exist."
    )
    decorator = pm.wait_computations_if_benchmark_mode

    # Some versions decide whether to wrap at decoration time based on BenchmarkMode.get().
    # To make this test runnable on both versions (and independent of global state),
    # we temporarily replace the imported BenchmarkMode with a controllable stub.
    old_benchmark_mode = getattr(pm, "BenchmarkMode", None)
    pm.BenchmarkMode = DummyBenchmarkMode
    try:

        class DummyPartition:
            def __init__(self):
                self.wait_calls = 0

            def wait(self):
                self.wait_calls += 1

        parts = np.array([[DummyPartition(), DummyPartition()]], dtype=object)

        def make_parts():
            return parts

        # Not in benchmark mode: should not call wait()
        DummyBenchmarkMode._value = False
        wrapped = decorator(make_parts)
        res = wrapped()
        assert res is parts, "Wrapped function must return the original partitions result."
        assert sum(p.wait_calls for p in parts.flatten()) == 0, (
            "Decorator should not call partition.wait() when BenchmarkMode.get() is False."
        )

        # In benchmark mode: should call wait() on each partition exactly once
        DummyBenchmarkMode._value = True
        wrapped = decorator(make_parts)
        res = wrapped()
        assert res is parts, "Wrapped function must return the original partitions result."
        assert [p.wait_calls for p in parts.flatten()] == [1, 1], (
            "Decorator should call partition.wait() once per partition when "
            "BenchmarkMode.get() is True."
        )
    finally:
        if old_benchmark_mode is None:
            delattr(pm, "BenchmarkMode")
        else:
            pm.BenchmarkMode = old_benchmark_mode