import re


def test_exchange_features_renamed_and_doc_updated():
    source = open("/workspace/tools/distpartitioning/data_shuffle.py", "r", encoding="utf-8").read()

    # 1) Function should be renamed to a generic name.
    assert "def exchange_features(" in source, (
        "Expected function to be renamed to a generic name `exchange_features` "
        "(review requested rename because it exchanges both node and edge features)."
    )

    # Ensure the old name isn't still present as a def (helps catch partial refactors).
    assert "def exchange_node_features(" not in source, (
        "Did not expect `exchange_node_features` to still be defined; it should be "
        "replaced by the generic `exchange_features`."
    )

    # 2) Signature should include a more meaningful feature container name: `feature_data`.
    m = re.search(r"def\s+exchange_features\s*\(([^)]*)\)\s*:", source)
    assert m, "Could not find `exchange_features` function signature to validate parameter naming."
    sig = m.group(1)
    assert "feature_data" in sig, (
        "Expected `exchange_features` signature to include a meaningful parameter name "
        "`feature_data` (review requested renaming ambiguous parameters). "
        f"Found signature: ({sig})"
    )

    # 3) Docstring parameters should be updated to include `feature_data` and `feat_type`.
    # (Review asked to update docstring of parameters; this is observable in source.)
    assert re.search(r"\n\s*feature_data\s*:\s*\w+", source), (
        "Expected docstring parameter section to include `feature_data: ...` "
        "after documentation update."
    )
    assert re.search(r"\n\s*feat_type\s*:\s*\w+", source), (
        "Expected docstring parameter section to include `feat_type: ...` "
        "after documentation update."
    )

    # The "after" code still contains the misspelling `node_feautres` elsewhere (e.g., other docstrings),
    # so we intentionally do NOT assert its absence globally.