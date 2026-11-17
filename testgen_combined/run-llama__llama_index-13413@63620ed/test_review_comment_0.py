import re


def test_rag_fusion_pipeline_does_not_use_service_context_for_index_or_query_engine():
    path = "/workspace/llama-index-packs/llama-index-packs-rag-fusion-query-pipeline/llama_index/packs/rag_fusion_query_pipeline/base.py"
    source = open(path, "r", encoding="utf-8").read()

    assert (
        "ServiceContext" not in source
    ), "ServiceContext should not be referenced/imported; it is deprecated and should be removed from this pack."

    assert (
        "service_context" not in source
    ), "The pack should not construct or pass a `service_context`; pass `embed_model` to VectorStoreIndex and `llm` to as_query_engine instead."

    assert (
        "VectorStoreIndex(nodes, embed_model=embed_model)" in source
    ), "Expected VectorStoreIndex to be constructed with `embed_model=embed_model` (instead of `service_context=...`)."

    assert (
        "as_query_engine(llm=self.llm)" in source
    ), "Expected query engine creation to explicitly pass `llm=self.llm` (instead of relying on a ServiceContext)."

    # Ensure we *don't* regress back to old patterns.
    assert not re.search(
        r"VectorStoreIndex\(\s*nodes\s*,\s*service_context\s*=",
        source,
        flags=re.MULTILINE,
    ), "VectorStoreIndex should not be created with `service_context=`."
    assert "as_query_engine()" not in source, (
        "as_query_engine should not be called without an explicit llm; "
        "it should be `as_query_engine(llm=self.llm)`."
    )