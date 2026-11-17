import inspect

import keep.topologies.topologies_service as ts


def test_get_all_topology_data_uses_snake_case_include_empty_deps_parameter():
    """
    Style check: parameter names should be snake_case (no leftovers like includeEmptyDeps).
    This test asserts the public API of TopologiesService.get_all_topology_data uses
    `include_empty_deps` (and not `includeEmptyDeps`).
    """
    sig = inspect.signature(ts.TopologiesService.get_all_topology_data)
    params = list(sig.parameters.keys())

    assert (
        "include_empty_deps" in params
    ), f"Expected parameter `include_empty_deps` in get_all_topology_data signature, got: {params}"
    assert (
        "includeEmptyDeps" not in params
    ), f"Found leftover camelCase parameter `includeEmptyDeps` in get_all_topology_data signature: {params}"