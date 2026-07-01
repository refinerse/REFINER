import re


def test_profit_commands_use_timezone_aware_utc_now_instead_of_utcnow():
    """
    Ensure RPC profit commands use timezone-aware UTC dates.

    This test enforces the review change:
    - Avoid datetime.utcnow().date() / datetime.utcnow().date().replace(...)
    - Use datetime.now(timezone.utc).date() instead.
    """
    source = open("/workspace/freqtrade/rpc/rpc.py", "r", encoding="utf-8").read()

    # Must not use utcnow() in the profit commands (daily/weekly/monthly).
    forbidden_patterns = [
        r"today\s*=\s*datetime\.utcnow\(\)\.date\(\)",
        r"first_day_of_month\s*=\s*datetime\.utcnow\(\)\.date\(\)\.replace\(",
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, source), (
            "Profit RPC commands must not use datetime.utcnow() (timezone-naive). "
            "Use datetime.now(timezone.utc) instead. "
            f"Found forbidden pattern: {pat}"
        )

    # Must use timezone-aware now(timezone.utc) for these assignments.
    required_patterns = [
        r"today\s*=\s*datetime\.now\(timezone\.utc\)\.date\(\)",
        r"first_day_of_month\s*=\s*datetime\.now\(timezone\.utc\)\.date\(\)\.replace\(",
    ]
    for pat in required_patterns:
        assert re.search(pat, source), (
            "Expected timezone-aware UTC date usage in profit RPC commands. "
            f"Missing required pattern: {pat}"
        )