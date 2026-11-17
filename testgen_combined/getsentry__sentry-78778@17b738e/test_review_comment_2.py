import re


def test_no_specific_analytics_provider_mentioned_in_api_analytics_module():
    source = open("/workspace/src/sentry/api/analytics.py", "r", encoding="utf-8").read()

    # Review comment: "best not to mention any specific analytics provider in our code"
    # The before-version included "amplitude(?)" in a comment; the fixed version removes it.
    assert "amplitude" not in source.lower(), (
        "src/sentry/api/analytics.py must not mention a specific analytics provider "
        "(e.g. 'amplitude') anywhere in the module."
    )


def test_devtoolbar_event_uses_api_request_naming():
    source = open("/workspace/src/sentry/api/analytics.py", "r", encoding="utf-8").read()

    # The addressed change renamed the event to DevToolbarApiRequestEvent and the type to
    # 'devtoolbar.api_request' (from DevToolbarRequestEvent / 'devtoolbar.request').
    assert re.search(r'^\s*class\s+DevToolbarApiRequestEvent\b', source, flags=re.MULTILINE), (
        "Expected DevToolbar analytics event class to be named DevToolbarApiRequestEvent."
    )
    assert 'type = "devtoolbar.api_request"' in source, (
        "Expected DevToolbar analytics event type to be 'devtoolbar.api_request'."
    )