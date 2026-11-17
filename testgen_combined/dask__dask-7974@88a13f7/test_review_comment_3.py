import re


def test_visualize_docstring_default_extension_mentions_png_not_svg():
    source = open("/workspace/dask/highlevelgraph.py", encoding="utf-8").read()

    # Extract the docstring of HighLevelGraph.visualize from source
    m = re.search(
        r"def\s+visualize\([^\)]*\):\n\s+\"\"\"(.*?)\n\s+\"\"\"",
        source,
        flags=re.S,
    )
    assert m is not None, "Could not locate HighLevelGraph.visualize docstring in /workspace/dask/highlevelgraph.py"
    doc = m.group(1)

    assert (
        "doesn't include an extension, '.png' will be used by default." in doc
    ), (
        "HighLevelGraph.visualize docstring should state that when filename has no "
        "extension, '.png' is used by default."
    )

    assert (
        "doesn't include an extension, '.svg' will be used by default." not in doc
    ), (
        "HighLevelGraph.visualize docstring must not claim '.svg' is the default "
        "extension when filename has no extension."
    )