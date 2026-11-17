import re


def test_custom_views_feature_flag_returns_404_not_405():
    source = open(
        "/workspace/src/sentry/issues/endpoints/organization_group_search_views.py",
        "r",
        encoding="utf-8",
    ).read()

    # Ensure we're checking the exact feature gate in this endpoint.
    assert (
        'features.has("organizations:issue-stream-custom-views", organization)' in source
    ), "Expected endpoint to gate behavior on the issue-stream-custom-views feature flag."

    # The style change: when feature is disabled, behave like the endpoint doesn't exist (404),
    # not method-not-allowed (405).
    assert (
        "HTTP_404_NOT_FOUND" in source
    ), "Expected feature-disabled behavior to return 404 (endpoint behaves as non-existent)."

    assert (
        "HTTP_405_METHOD_NOT_ALLOWED" not in source
    ), "Did not expect feature-disabled behavior to return 405; 405 is for disallowed HTTP methods."