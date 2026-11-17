import inspect

import dask.base


def test_visualize_docstring_mentions_multiple_graphs():
    """
    The review comment clarifies that dask.base.visualize accepts multiple graphs,
    so its docstring should describe visualizing several graphs at once (not a single one).
    """
    doc = inspect.getdoc(dask.base.visualize)
    assert doc is not None, "Expected dask.base.visualize to have a docstring"

    first_line = doc.splitlines()[0].strip()
    assert "several" in first_line.lower(), (
        "dask.base.visualize docstring should state it can visualize *several* low level "
        f"dask graphs at once. Got first line: {first_line!r}"
    )
    assert "at once" in first_line.lower(), (
        "dask.base.visualize docstring should indicate multiple graphs can be visualized "
        f"in a single call (e.g., 'at once'). Got first line: {first_line!r}"
    )