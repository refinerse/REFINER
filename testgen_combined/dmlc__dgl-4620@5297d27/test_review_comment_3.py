import re


def test_edge_id_variable_names_are_descriptive():
    source = open("/workspace/tools/distpartitioning/dataset_utils.py", "r", encoding="utf-8").read()

    # The review comment asks for better names than df_0/df_1 in the edge-reading loop.
    # Before: df_0 = []; df_1 = []
    # After:  src_ids = []; dst_ids = []
    assert "src_ids = []" in source and "dst_ids = []" in source, (
        "Expected descriptive variable names for edge endpoints: "
        "the edge-reading loop should use `src_ids` and `dst_ids` lists "
        "instead of generic `df_0`/`df_1`."
    )

    # Make sure we didn't keep the old generic names around.
    assert re.search(r"\bdf_0\s*=\s*\[\s*\]", source) is None and re.search(
        r"\bdf_1\s*=\s*\[\s*\]", source
    ) is None, (
        "Found `df_0 = []` and/or `df_1 = []` in dataset_utils.py. "
        "These generic names should be replaced with `src_ids`/`dst_ids`."
    )