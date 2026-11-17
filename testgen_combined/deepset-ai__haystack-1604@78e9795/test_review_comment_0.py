import re


def test_delete_labels_docstring_and_signature_aligned_with_delete_documents():
    """
    This test enforces that SQLDocumentStore.delete_labels() is aligned with delete_documents()
    by supporting an optional `ids` parameter and documenting it in the docstring.
    """
    source = open("/workspace/haystack/document_store/sql.py", "r", encoding="utf-8").read()

    # 1) Signature must include ids: Optional[List[str]] = None
    sig_pattern = re.compile(
        r"def\s+delete_labels\s*\(\s*self\s*,\s*index\s*:\s*Optional\s*\[\s*str\s*\]\s*=\s*None\s*,"
        r"\s*ids\s*:\s*Optional\s*\[\s*List\s*\[\s*str\s*\]\s*\]\s*=\s*None\s*,"
        r"\s*filters\s*:\s*Optional\s*\[\s*Dict\s*\[\s*str\s*,\s*List\s*\[\s*str\s*\]\s*\]\s*\]\s*=\s*None\s*\)",
        re.MULTILINE,
    )
    assert sig_pattern.search(source), (
        "SQLDocumentStore.delete_labels() must accept an optional `ids: Optional[List[str]] = None` parameter "
        "and place it between `index` and `filters`, mirroring delete_documents()."
    )

    # 2) Docstring must include an `:param ids:` entry
    assert ":param ids:" in source, (
        "The delete_labels() docstring must document the new `ids` parameter with a ':param ids:' entry."
    )

    # 3) Implementation should handle the 'no filters and no ids' case explicitly (aligned with delete_documents())
    assert "if not filters and not ids" in source, (
        "delete_labels() should explicitly handle the case 'if not filters and not ids' "
        "to delete all labels in the index, aligned with delete_documents()."
    )