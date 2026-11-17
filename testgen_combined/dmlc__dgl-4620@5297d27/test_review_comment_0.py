import re


def test_get_idranges_docstring_and_signature_updated_for_num_chunks_optional():
    """
    This test enforces the review-requested change:
    - The parameter after ':' in the docstring should be a type (e.g., 'int, optional').
    - The description should be reworded to be clearer.
    Concretely, get_idranges should use 'num_chunks=None' and document it as 'int, optional'
    with the clarified "merge ID ranges" wording.
    """
    source = open("/workspace/tools/distpartitioning/utils.py", "r", encoding="utf-8").read()

    # 1) Signature changed from expected_num_chunks (required) -> num_chunks=None (optional)
    assert (
        "def get_idranges(names, counts, num_chunks=None)" in source
    ), (
        "Expected get_idranges to accept optional 'num_chunks=None' (after fix). "
        "Before-fix code used a required 'expected_num_chunks' parameter."
    )

    # 2) Docstring parameter line should include the type after colon, and be 'int, optional'
    # Use a tolerant regex across whitespace/newlines.
    assert re.search(r"\n\s*num_chunks\s*:\s*int,\s*optional\s*\n", source), (
        "Expected docstring to specify the type after ':' for num_chunks as 'int, optional'. "
        "Before-fix docstring used 'expected_num_chunks : expected number...' (no type)."
    )

    # 3) Docstring description should be reworded to clarify behavior ("merge ID ranges")
    assert "we'd like to merge ID ranges into specific number" in source, (
        "Expected reworded docstring description explaining that ID ranges are merged "
        "into a specific number of chunks. Before-fix wording about collapsing chunks "
        "was unclear."
    )