import importlib


def test_layernorm_builder_class_and_metadata_renamed():
    mod = importlib.import_module("op_builder.layernorm")

    # The review fix renames the builder to match what it actually builds.
    assert hasattr(mod, "LayerNormBuilder"), (
        "op_builder.layernorm must define 'LayerNormBuilder' (builder for layernorm op). "
        "This ensures the class name matches the module purpose and built sources."
    )

    LayerNormBuilder = getattr(mod, "LayerNormBuilder")
    assert getattr(LayerNormBuilder, "NAME", None) == "layernorm", (
        "LayerNormBuilder.NAME must be 'layernorm' (not 'fused_optim'); "
        "the builder name should reflect the layernorm op it builds."
    )
    assert getattr(LayerNormBuilder, "PREBUILT_IMPORT_PATH", None) == "colossalai._C.layernorm", (
        "LayerNormBuilder.PREBUILT_IMPORT_PATH must be 'colossalai._C.layernorm' "
        "(not 'colossalai._C.fused_optim') to match the layernorm extension."
    )