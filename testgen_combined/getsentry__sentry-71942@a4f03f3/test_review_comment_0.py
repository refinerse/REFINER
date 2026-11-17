import re


def test_default_views_uses_sortoptions_enum_value_for_querysort():
    source = open(
        "/workspace/src/sentry/issues/endpoints/organization_group_search_views.py",
        encoding="utf-8",
    ).read()

    # Style requirement from review: use the enum directly rather than a raw string,
    # i.e. `SortOptions.DATE.value` instead of `"date"`.
    assert (
        "querySort" in source
    ), "Expected DEFAULT_VIEWS to define a 'querySort' key in organization_group_search_views.py"

    assert (
        '"querySort": SortOptions.DATE.value' in source
    ), "Expected DEFAULT_VIEWS['querySort'] to use the enum value: SortOptions.DATE.value (not a raw string like 'date')."

    assert (
        '"querySort": "date"' not in source
    ), "Found legacy string literal for querySort ('date'); expected enum usage via SortOptions.DATE.value."

    # Extra guard: ensure SortOptions is imported from the correct module.
    assert re.search(
        r"from\s+sentry\.models\.savedsearch\s+import\s+SortOptions", source
    ), "Expected SortOptions to be imported (from sentry.models.savedsearch import SortOptions) to support enum usage."