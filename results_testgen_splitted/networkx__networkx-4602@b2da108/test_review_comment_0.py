import pytest
import networkx as nx
from networkx.algorithms.centrality.betweenness import betweenness_centrality


class UnsortableNode:
    """A node type that is hashable/equatable but not orderable.

    Using sorted(G.nodes()) should raise TypeError in Python 3.
    """

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return f"UnsortableNode({self.label!r})"

    def __hash__(self):
        return hash(self.label)

    def __eq__(self, other):
        return isinstance(other, UnsortableNode) and self.label == other.label


def test_betweenness_centrality_k_does_not_require_sortable_nodes():
    G = nx.path_graph([UnsortableNode(i) for i in range(6)])

    # When k is not None, the implementation should sample from a list of nodes.
    # This must not require that nodes be sortable/orderable.
    try:
        result = betweenness_centrality(G, k=3, seed=1)
    except TypeError as e:
        pytest.fail(
            "betweenness_centrality should not sort nodes when k is provided; "
            "it must work for graphs with non-orderable node objects. "
            f"Got TypeError: {e}"
        )

    assert isinstance(result, dict) and set(result) == set(
        G.nodes()
    ), "betweenness_centrality should return a dict with all graph nodes as keys."