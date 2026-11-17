import re


def test_default_views_typed_and_keys_match_serializer_response():
    source = open(
        "/workspace/src/sentry/issues/endpoints/organization_group_search_views.py",
        encoding="utf-8",
    ).read()

    # The review comment asks for a way to guarantee keys are correct.
    # The addressed change does this by typing DEFAULT_VIEWS as
    # `list[GroupSearchViewSerializerResponse]` and including the extra
    # serializer response keys in the default dicts.
    assert (
        "GroupSearchViewSerializerResponse" in source
    ), "Expected DEFAULT_VIEWS to be tied to the serializer response type (GroupSearchViewSerializerResponse)."

    assert re.search(
        r"DEFAULT_VIEWS\s*:\s*list\[\s*GroupSearchViewSerializerResponse\s*\]\s*=",
        source,
    ), (
        "Expected DEFAULT_VIEWS to have an explicit type annotation "
        "of list[GroupSearchViewSerializerResponse] so key correctness is enforced."
    )

    # Ensure the default dict includes keys that would be easy to forget when columns/fields change.
    # In the fixed code, these keys are present (with None values).
    assert '"dateCreated"' in source and '"dateUpdated"' in source, (
        "Expected DEFAULT_VIEWS entries to include serializer response keys "
        '"dateCreated" and "dateUpdated" to reduce risk of missing fields.'
    )

    # Also ensure querySort uses SortOptions.DATE.value rather than an untyped string.
    assert "SortOptions.DATE.value" in source, (
        "Expected DEFAULT_VIEWS['querySort'] to use SortOptions.DATE.value (typed enum value) "
        "instead of a raw string like 'date'."
    )