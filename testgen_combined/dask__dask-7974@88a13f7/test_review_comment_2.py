import inspect

import dask.base


def test_visualize_docstring_documents_args_parameter_not_dsk():
    """
    The review comment indicates that visualize(*args, **kwargs) accepts one or more
    dask graphs/collections via *args. The docstring should document the parameter
    as `args`, not `dsk`.
    """
    doc = inspect.getdoc(dask.base.visualize)
    assert doc is not None and "Parameters" in doc, "visualize() must have a docstring with a Parameters section"

    assert "args : dict(s) or collection(s)" in doc, (
        "visualize() docstring must document its positional parameter as `args` (one or more "
        "graphs/collections passed via *args), not as `dsk`."
    )
    assert "dsk : dict(s) or collection(s)" not in doc, (
        "visualize() docstring should not mention a `dsk` parameter, since visualize() accepts "
        "graphs/collections via *args."
    )