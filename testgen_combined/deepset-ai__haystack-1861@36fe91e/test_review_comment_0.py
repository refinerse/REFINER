import re


def test_headers_type_hints_use_plain_dict_not_mutablemapping():
    """
    The review change replaced user-facing `headers` type hints from `MutableMapping[str, str]`
    to the simpler `Optional[Dict[str, str]]`.
    This test enforces that `headers` parameters are NOT annotated as MutableMapping anywhere
    in haystack/document_stores/elasticsearch.py.
    """
    source_path = "/workspace/haystack/document_stores/elasticsearch.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Must fail on "before" because the file contains headers: MutableMapping[str, str] in many signatures.
    assert "headers: MutableMapping[str, str]" not in source, (
        "Expected headers type hints to not use MutableMapping (user-facing parameter should use plain dict), "
        "but found 'headers: MutableMapping[str, str]' in /workspace/haystack/document_stores/elasticsearch.py. "
        "Please change to Optional[Dict[str, str]] (or equivalent plain dict typing)."
    )

    # Stronger check: the typing import should not include MutableMapping anymore.
    # (Still allows MutableMapping to exist in docstrings/comments, but ensures it's not imported as a typing hint.)
    typing_import_line = re.search(r"^from typing import .*$", source, flags=re.MULTILINE)
    assert typing_import_line is not None, "Expected a 'from typing import ...' line in the module."
    assert "MutableMapping" not in typing_import_line.group(0), (
        "Expected 'MutableMapping' to be removed from the typing imports after switching headers to Dict[str, str], "
        f"but it is still imported: {typing_import_line.group(0)!r}"
    )