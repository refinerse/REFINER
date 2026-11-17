import re


def test_uuid_to_object_cast_missing_id_in_set_raises_and_regex_is_generic():
    """
    Verify the reviewed test was updated to cover the "set of ids where one is
    missing" case and that the error regex is not the old, too-specific string.

    This is a source-inspection test because importing /workspace/tests/test_edgeql_casts.py
    fails in this environment (no 'edgedb' module).
    """
    source = open("/workspace/tests/test_edgeql_casts.py", "r", encoding="utf-8").read()

    # 1) The updated test should define a dummy_uuid variable (new behavior).
    assert "dummy_uuid = '1' * 32" in source, (
        "Expected test_edgeql_casts_uuid_to_object to define dummy_uuid, as in "
        "the reviewed update. This indicates the test was revised."
    )

    # 2) The updated test should check that casting a set where one uuid is missing
    # raises CardinalityViolationError (the review request).
    # We look for the specific query block where persons[0].id and dummy_uuid are passed.
    pattern_missing_in_set = re.compile(
        r"assertRaisesRegexTx\(\s*"
        r"edgedb\.CardinalityViolationError,\s*r'with id \.\* does not exist'\s*"
        r"\)\s*:\s*"
        r"await self\.con\.query\(\s*"
        r"'''[\s\S]*?"
        r"select\s*\(<Person>\{\s*<uuid>\$0,\s*<uuid>\$1\s*\}\)\s*\{\s*name\s*\}"
        r"[\s\S]*?"
        r"'''\s*,\s*persons\[0\]\.id\s*,\s*dummy_uuid\s*"
        r"\)",
        re.MULTILINE,
    )
    assert pattern_missing_in_set.search(source), (
        "Expected an assertRaisesRegexTx block that executes the set-cast query "
        "with variables (persons[0].id, dummy_uuid), asserting a "
        "CardinalityViolationError. This is the key behavior requested in review."
    )

    # 3) The old error regex should be gone, since it was replaced to bind anchors
    # correctly and be less specific.
    assert "with this id does not exist" not in source, (
        "Found old error regex 'with this id does not exist'. The reviewed change "
        "replaced it with a generic 'with id .* does not exist' form."
    )