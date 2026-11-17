import re


def test_debug_challenges_config_mock_includes_verbose_count_inline():
    """
    Style regression test for certbot/tests/auth_handler_test.py:
    Ensure config mock in test_debug_challenges is created with verbose_count=0
    in the same call, rather than assigned in a separate statement.
    """
    path = "/workspace/certbot/tests/auth_handler_test.py"
    source = open(path, "r", encoding="utf-8").read()

    # Narrow to the body of the specific test function to avoid false positives.
    m = re.search(
        r"def\s+test_debug_challenges\s*\([^)]*\):(?P<body>.*?)(?:\n\s+def\s|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert m is not None, "Expected to find def test_debug_challenges(...) in /workspace/certbot/tests/auth_handler_test.py"

    body = m.group("body")

    assert "config = mock.Mock(debug_challenges=True, verbose_count=0)" in body, (
        "Expected test_debug_challenges to construct config with "
        "mock.Mock(debug_challenges=True, verbose_count=0) inline (style change)."
    )

    assert "config = mock.Mock(debug_challenges=True)\n" not in body, (
        "Did not expect test_debug_challenges to construct config with only debug_challenges=True; "
        "verbose_count should be passed inline as well."
    )
    assert "config.verbose_count = 0" not in body, (
        "Did not expect a separate assignment 'config.verbose_count = 0' in test_debug_challenges; "
        "verbose_count should be passed inline to mock.Mock(...)."
    )