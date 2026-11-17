def test_visualize_docstring_none_filename_mentions_jupyter_only_render():
    source = open("/workspace/dask/highlevelgraph.py", "r", encoding="utf-8").read()

    # The review comment asked to use `None` to avoid writing a file, e.g. in a Jupyter notebook.
    # The "after" docstring was changed to explicitly say the graph is rendered in Jupyter only.
    # The "before" docstring instead talked about "communicate with dot using only pipes."
    expected = "rendered in the Jupyter notebook only"
    forbidden_before_phrase = "communicate\n            with dot using only pipes"

    assert expected in source, (
        "HighLevelGraph.visualize docstring should explicitly state that when "
        "filename is None, no file is written and the graph is rendered in the "
        "Jupyter notebook only."
    )
    assert forbidden_before_phrase not in source, (
        "HighLevelGraph.visualize docstring should no longer describe filename=None "
        "as communicating with dot using only pipes; it should describe Jupyter-only rendering."
    )