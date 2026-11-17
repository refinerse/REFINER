import re


def test_parsr_convert_initializes_meta_when_none_at_start_of_method():
    """
    Style requirement: initialize/normalize parameters at the beginning of ParsrConverter.convert,
    specifically ensure meta is checked for None and set to {} early, rather than later conditional
    re-assignment like `meta = meta if meta else {}`.
    """
    source = open("/workspace/haystack/nodes/file_converter/parsr.py", "r", encoding="utf-8").read()

    # Extract convert() method block (best-effort via simple regex; no AST parsing)
    m = re.search(r"\n\s*def convert\([\s\S]*?\n\s*def _get_paragraph_string\(", source)
    assert m, "Could not locate ParsrConverter.convert method block in parsr.py"
    convert_block = m.group(0)

    # The "after" version initializes meta early with:
    #   if meta is None:
    #       meta = {}
    assert (
        "if meta is None:\n            meta = {}" in convert_block
        or "if meta is None:\n            meta = {}" in convert_block.replace("\r\n", "\n")
    ), (
        "Expected ParsrConverter.convert to initialize meta at the start of the method with:\n"
        "    if meta is None:\n"
        "        meta = {}\n"
        "This ensures meta is never None before being mutated."
    )

    # The "before" version used a late/conditional initialization:
    #   meta = meta if meta else {}
    assert "meta = meta if meta else {}" not in convert_block, (
        "Found late conditional meta initialization `meta = meta if meta else {}` in ParsrConverter.convert. "
        "Expected meta to be normalized using an explicit `if meta is None: meta = {}` near the top."
    )