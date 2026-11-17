import re


def test_devtoolbar_middleware_class_is_named_devtoolbaranalyticsmiddleware():
    source = open("/workspace/src/sentry/middleware/devtoolbar.py").read()

    # Style requirement from review: class should be named with DevToolbarAnalytics + Middleware suffix.
    assert (
        re.search(r"^\s*class\s+DevToolbarAnalyticsMiddleware\b", source, flags=re.MULTILINE)
        is not None
    ), (
        "Expected middleware class to be named 'DevToolbarAnalyticsMiddleware' (per review: "
        "'DevToolBarAnalytics' + keep 'Middleware' suffix)."
    )

    # Ensure the old/generic name is gone.
    assert (
        re.search(r"^\s*class\s+AnalyticsMiddleware\b", source, flags=re.MULTILINE) is None
    ), "Did not expect legacy class name 'AnalyticsMiddleware' to remain in devtoolbar middleware module."