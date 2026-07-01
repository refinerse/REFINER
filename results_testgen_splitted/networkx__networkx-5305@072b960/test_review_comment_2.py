import networkx as nx


def test_weighted_distance_graph_edges_have_multiple_weight_attributes_in_test_fixture():
    """
    The reviewed change expanded the weighted-distance test fixture graph to
    include additional edge attributes: 'cost' and 'high_cost' (in addition to
    'weight'). This test locks in that specific change by inspecting the
    repository's own test fixture graph definition.

    It MUST fail on the "before" version because those attributes were not added.
    It MUST pass on the "after" version because they are present on every edge.
    """
    # Import the repository test module (it is importable in this environment).
    import networkx.algorithms.tests.test_distance_measures as tdm

    # Instantiate the fixture class and run its setup_method to build the graph.
    twd = tdm.TestWeightedDistance()
    twd.setup_method()
    G = twd.G

    # Strong, specific assertions for what changed in the diff:
    # edges now must carry 'cost' and 'high_cost' attributes (alongside 'weight').
    for u, v, data in G.edges(data=True):
        assert "weight" in data, f"Edge {(u, v)} is missing required 'weight' attribute."
        assert (
            "cost" in data
        ), f"Edge {(u, v)} is missing newly-added 'cost' attribute in weighted test fixture."
        assert (
            "high_cost" in data
        ), f"Edge {(u, v)} is missing newly-added 'high_cost' attribute in weighted test fixture."

        # And specifically, in the updated fixture these were set equal/proportional:
        assert (
            data["cost"] == data["weight"]
        ), f"Edge {(u, v)} expected 'cost' == 'weight' in updated fixture."
        assert (
            data["high_cost"] == data["weight"] * 10
        ), f"Edge {(u, v)} expected 'high_cost' == 10 * 'weight' in updated fixture."