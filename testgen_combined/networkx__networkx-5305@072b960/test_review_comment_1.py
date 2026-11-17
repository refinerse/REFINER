import pytest

import networkx as nx


def test_weighted_distance_uses_pytest_approx_in_radius_tests():
    """
    The review comment removed/avoided assertions that explicitly test for
    floating-point round-off (e.g., `!= 0.9`) and instead relies on pytest.approx.

    This test enforces that the weighted-distance "radius" tests in
    `networkx/algorithms/tests/test_distance_measures.py` do NOT include
    the anti-pattern `!= 0.9` (which asserts round-off occurs), and instead
    use `pytest.approx(...) == 0.9`.
    """
    path = "/workspace/networkx/algorithms/tests/test_distance_measures.py"
    source = open(path, "r", encoding="utf-8").read()

    assert "class TestWeightedDistance:" in source, "Sanity check: expected TestWeightedDistance in the target file."

    # Before code contains these exact lines, which assert round-off occurs.
    assert (
        "assert nx.radius(self.G) != 0.9" not in source
    ), "Radius tests should not assert `!= 0.9` (testing round-off); they should use pytest.approx instead."

    assert (
        "assert nx.radius(self.G, usebounds=True) != 0.9" not in source
    ), "Bound radius tests should not assert `!= 0.9` (testing round-off); they should use pytest.approx instead."

    # Ensure the intended idiom is present (at least once) in the weighted-distance tests.
    assert (
        "pytest.approx(nx.radius(self.G" in source
    ), "Expected weighted-distance radius tests to use `pytest.approx(nx.radius(...))` for float comparisons."

    # Also do a quick runtime sanity check that radius is close to 0.9 for the classic weights.
    # (This should be true on both versions; the behavior change is in the tests, not algorithm.)
    G = nx.Graph()
    G.add_edge(0, 1, weight=0.6)
    G.add_edge(0, 2, weight=0.2)
    G.add_edge(2, 3, weight=0.1)
    G.add_edge(2, 4, weight=0.7)
    G.add_edge(2, 5, weight=0.9)
    G.add_edge(1, 5, weight=0.3)

    r = nx.radius(G, weight="weight")
    assert pytest.approx(r) == 0.9, f"Sanity check failed: expected weighted radius ~0.9, got {r!r}"