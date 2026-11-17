import re


def test_groupsearchview_serializer_has_typed_response_and_return_annotation():
    source_path = "/workspace/src/sentry/api/serializers/models/groupsearchview.py"
    source = open(source_path).read()

    # The review asks to "add a response type" and the addressed code uses a TypedDict
    # plus a return type annotation on serialize().
    assert "class GroupSearchViewSerializerResponse(TypedDict):" in source, (
        "Expected GroupSearchViewSerializerResponse TypedDict to be defined to document "
        "the serializer response shape."
    )

    # Ensure serialize has a return annotation to that response type and supports **kwargs.
    pattern = (
        r"def\s+serialize\s*\(\s*self\s*,\s*obj\s*,\s*attrs\s*,\s*user\s*,\s*\*\*kwargs\s*\)"
        r"\s*->\s*GroupSearchViewSerializerResponse\s*:"
    )
    assert re.search(pattern, source), (
        "Expected GroupSearchViewSerializer.serialize to accept **kwargs and declare a return "
        "type of GroupSearchViewSerializerResponse for documented/typed serializer output."
    )