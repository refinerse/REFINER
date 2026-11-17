import networkx as nx


def test_distance_measures_default_weight_is_unweighted_even_if_weight_attr_present():
    """
    Regression test: default `weight` for distance-measure functions must be None,
    so graphs with an edge attribute named "weight" do not silently change results.
    """
    G = nx.Graph()
    G.add_edge(0, 1, weight=10)

    # With unweighted distances (the historical/default behavior), distances are 1 hop.
    expected = 1

    # These should all default to unweighted computations when `weight` is not provided.
    assert (
        nx.diameter(G) == expected
    ), "nx.diameter(G) should ignore edge attribute 'weight' by default (weight=None)."
    assert (
        nx.radius(G) == expected
    ), "nx.radius(G) should ignore edge attribute 'weight' by default (weight=None)."
    assert (
        nx.eccentricity(G)[0] == expected
    ), "nx.eccentricity(G) should ignore edge attribute 'weight' by default (weight=None)."
    assert (
        nx.periphery(G) == [0, 1]
    ), "nx.periphery(G) should be computed unweighted by default (both nodes peripheral in a 2-node graph)."
    assert (
        nx.center(G) == [0, 1]
    ), "nx.center(G) should be computed unweighted by default (both nodes central in a 2-node graph)."

    # Sanity check: if the user explicitly asks for weight="weight", results should differ here.
    assert nx.diameter(G, weight="weight") == 10, (
        "When explicitly requesting weight='weight', nx.diameter should use the edge "
        "attribute and return the weighted distance."
    )