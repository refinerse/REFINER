import inspect

import lib.matplotlib.cm as cm


def test_colormapregistry_get_cmap_docstring_first_line_style():
    """
    Style regression test: the first line of the get_cmap docstring should be
    the succinct summary sentence requested in review.
    """
    doc = inspect.getdoc(cm.ColormapRegistry.get_cmap)
    assert doc is not None, "Expected ColormapRegistry.get_cmap to have a docstring."

    first_line = doc.splitlines()[0].strip()
    assert first_line == "Return a color map specified through *cmap*.", (
        "ColormapRegistry.get_cmap docstring summary line should be exactly "
        "'Return a color map specified through *cmap*.' (style requirement). "
        f"Got: {first_line!r}"
    )