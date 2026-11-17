import re


def test_preprocessor_max_chars_check_rename_and_warning_message():
    source = open("/workspace/haystack/nodes/preprocessor/preprocessor.py", "r", encoding="utf-8").read()

    # 1) Variable rename: max_chars -> max_chars_check (clear it's only a check)
    assert "max_chars_check" in source, (
        "Expected PreProcessor to use the renamed parameter/attribute 'max_chars_check' "
        "to clarify this is only used for checking unusually long documents."
    )
    assert "max_chars:" not in source, (
        "Did not expect 'max_chars' parameter name to remain; it should be renamed to 'max_chars_check'."
    )

    # 2) Warning message should fix typo 'lenght' -> 'length' and add a clearer explanation.
    assert "maximum lenght" not in source, (
        "Expected typo to be fixed in warning message: 'lenght' should be 'length'."
    )

    assert "Something might be wrong with the splitting" in source, (
        "Expected warning message to be improved to clarify that exceeding the max length is only a warning "
        "and suggests splitting might be wrong."
    )

    # 3) Behavioral placement: after the review, process() should NOT call _long_documents on the whole ret,
    # but _process_single() should call it on split_documents.
    assert "self._long_documents(ret" not in source, (
        "Expected process() to no longer call _long_documents(ret, ...); "
        "the long-document check should happen per single-document processing after splitting."
    )

    assert re.search(r"self\._long_documents\(\s*split_documents\s*,\s*max_chars_check\s*=\s*self\.max_chars_check\s*\)", source), (
        "Expected _process_single() to call _long_documents(split_documents, max_chars_check=self.max_chars_check) "
        "to check the length of each split output."
    )