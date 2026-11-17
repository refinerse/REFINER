import re


def test_debug_challenges_config_mock_sets_verbose_count_inline():
    """
    Verify the review-requested behavior: the debug_challenges test should create
    the config mock with verbose_count passed inline, not assigned afterwards.

    This must fail on the "before" code (uses two statements) and pass on the
    "after" code (uses mock.Mock(debug_challenges=True, verbose_count=0)).
    """
    source = open("/workspace/certbot/tests/auth_handler_test.py", encoding="utf-8").read()

    # Locate the test_debug_challenges function body (simple regex-based extraction).
    m = re.search(
        r"(?ms)^\s*def\s+test_debug_challenges\s*\(self\)\s*:\s*\n(.*?)(?=^\s*def\s|\Z)",
        source,
    )
    assert m, "Expected to find a definition for test_debug_challenges(self) in auth_handler_test.py"

    body = m.group(1)

    assert "mock.Mock(debug_challenges=True, verbose_count=0)" in body, (
        "Expected test_debug_challenges to construct config as "
        "mock.Mock(debug_challenges=True, verbose_count=0) (inline verbose_count)."
    )

    assert "config.verbose_count = 0" not in body, (
        "Expected test_debug_challenges to NOT set config.verbose_count in a separate statement; "
        "verbose_count should be passed to mock.Mock inline."
    )