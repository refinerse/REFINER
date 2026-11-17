def test_get_or_generate_keys_docstring_spells_absolute_correctly():
    # This review comment is purely about a typo in the docstring.
    # There is no reliable runtime behavior difference, so we assert on source.
    source = open("/workspace/sky/authentication.py", "r", encoding="utf-8").read()

    assert (
        "Returns the aboslute public and private key paths." in source
        or "Returns the absolute public and private key paths." in source
    ), (
        "Test expects get_or_generate_keys() docstring to describe returning "
        "absolute/aboslute key paths. Source did not contain either phrase."
    )

    assert "abosulte" not in source, (
        "Typo regression: get_or_generate_keys() docstring should not contain "
        "'abosulte' (misspelling of 'absolute')."
    )