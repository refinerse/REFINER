import re


def test_base_document_store_uses_explicit_headers_instead_of_kwargs():
    """
    This test enforces the review-requested change:
    document store base class APIs should not use **kwargs to accommodate optional HTTP headers.
    Instead, they must expose an explicit `headers: Optional[Dict[str, str]] = None` parameter.
    """
    source = open("/workspace/haystack/document_stores/base.py", "r", encoding="utf-8").read()

    # Core behavior change: get_all_documents must have explicit `headers` param, not **kwargs.
    assert "def get_all_documents(" in source, "Sanity check: BaseDocumentStore.get_all_documents definition not found."

    # Fail "before": signature contains **kwargs.
    # Pass "after": signature contains `headers: Optional[Dict[str, str]] = None` and no **kwargs.
    get_all_docs_sig = re.search(r"def get_all_documents\((?P<sig>[\s\S]*?)\)\s*->\s*List\[Document\]\s*:", source)
    assert get_all_docs_sig, "Could not locate get_all_documents(...) signature block for inspection."

    sig = get_all_docs_sig.group("sig")

    assert "**kwargs" not in sig, (
        "get_all_documents() should not accept **kwargs; the review asked to avoid **kwargs and use an explicit "
        "`headers` keyword parameter instead."
    )
    assert re.search(r"\bheaders\s*:\s*Optional\s*\[\s*Dict\s*\[\s*str\s*,\s*str\s*\]\s*\]\s*=\s*None\b", sig), (
        "get_all_documents() must accept an explicit `headers: Optional[Dict[str, str]] = None` parameter "
        "to pass HTTP headers to supported document stores."
    )