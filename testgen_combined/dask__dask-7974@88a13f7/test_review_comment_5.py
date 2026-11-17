import inspect

import dask.highlevelgraph


def test_highlevelgraph_visualize_docstring_refers_to_this_graph_not_dask_graphs():
    doc = inspect.getdoc(dask.highlevelgraph.HighLevelGraph.visualize)
    assert doc is not None, "Expected HighLevelGraph.visualize to have a docstring."

    assert (
        "Visualize this dask high level graph." in doc
    ), (
        "HighLevelGraph.visualize docstring should describe visualizing 'this' high level graph, "
        "not refer generically to 'a dask high level graph' / 'dask graph(s)'. "
        f"Docstring was:\n{doc}"
    )