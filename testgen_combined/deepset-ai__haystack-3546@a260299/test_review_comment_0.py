import re


def test_multimodal_retriever_retrieve_batch_no_longer_uses_type_ignore_for_query_embs():
    """
    The review change removes the `# type: ignore` on the `query_embs=query_embeddings` argument.
    This test enforces that `query_by_embedding_batch` is called with `query_embs=query_embeddings`
    without `# type: ignore` on the same line.

    Fails on before-code (has `query_embs=query_embeddings,  # type: ignore`)
    Passes on after-code (has `query_embs=query_embeddings,`).
    """
    source = open("/workspace/haystack/nodes/retriever/multimodal/retriever.py", "r", encoding="utf-8").read()

    assert "query_by_embedding_batch" in source, "Expected retrieve_batch to call query_by_embedding_batch()."

    # Must exist: query_embs=query_embeddings argument
    assert (
        "query_embs=query_embeddings" in source
    ), "Expected retrieve_batch to pass query_embs=query_embeddings to query_by_embedding_batch()."

    # Must NOT exist: the same argument line with a type ignore comment
    assert (
        "query_embs=query_embeddings,  # type: ignore" not in source
    ), "Expected query_embs=query_embeddings to be passed without '# type: ignore' (it was removed in the fix)."

    # Also ensure we didn't just remove the whole line and replace with something else.
    # Require a line that contains the argument and ends with a comma (optionally with whitespace),
    # but not with any inline comment.
    pattern = r"^\s*query_embs=query_embeddings,\s*(#.*)?$"
    matches = re.findall(pattern, source, flags=re.MULTILINE)
    assert matches, "Expected to find a line 'query_embs=query_embeddings,' in the source."
    assert all(
        m == "" for m in matches
    ), "Expected 'query_embs=query_embeddings,' line to have no inline comment (especially not '# type: ignore')."