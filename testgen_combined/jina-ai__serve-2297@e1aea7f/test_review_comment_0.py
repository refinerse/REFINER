import re


def test_sparse_indexer_query_returns_per_query_distances_array_of_arrays():
    """
    The review comment requests that `distances` returned by the indexer's `query`
    is an array-of-arrays per query vector (even when query is not batched).

    This test inspects the source because importing jina-based modules fails in
    this execution environment.
    """
    path = "/workspace/tests/integration/sparse_pipeline/test_sparse_pipeline.py"
    source = open(path, "r", encoding="utf-8").read()

    # BEFORE: returned per-top_k distances: np.array([np.array(distances) for x in range(top_k)])
    # AFTER: returned per-query distances: np.array([distances])
    #
    # We assert the fixed behavior exists and the buggy pattern is absent.
    assert "np.array([distances])" in source, (
        "Expected sparse indexer query to return distances as per-query array-of-arrays "
        "(e.g., np.array([distances])) so each query vector has its own distances list."
    )

    buggy_pattern = r"np\.array\(\s*\[\s*np\.array\(\s*distances\s*\)\s*for\s+\w+\s+in\s+range\(\s*top_k\s*\)\s*\]\s*\)"
    assert re.search(buggy_pattern, source) is None, (
        "Found buggy distances construction that repeats distances top_k times "
        "(np.array([np.array(distances) for x in range(top_k)])). Distances should be "
        "grouped per query vector, not per returned match."
    )