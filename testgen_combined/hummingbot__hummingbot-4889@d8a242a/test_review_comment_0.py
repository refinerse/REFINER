import re


def test_mexc_tests_eliminate_waiting_with_timeout_helper_and_no_asyncio_sleep_in_listener_tests():
    """
    Verifies the review-requested change: eliminate explicit waiting (asyncio.sleep)
    in the mexc exchange tests by using the same approach as previous tests
    (a timeout helper + event-driven completion).

    This test is intentionally source-inspection based because importing the module
    fails in this environment due to missing optional dependency `ujson`.
    """
    source_path = "/workspace/test/hummingbot/connector/exchange/mexc/test_mexc_exchange.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # 1) After change, a helper exists to run coroutines with timeout (async_run_with_timeout),
    # which is used in place of "yield processor" sleeps.
    assert (
        "def async_run_with_timeout" in source
    ), (
        "Expected the tests to define an 'async_run_with_timeout' helper to avoid arbitrary waiting; "
        "this helper is missing."
    )

    # 2) After change, the listener tests should not rely on arbitrary sleeps to yield control.
    # We specifically look for the old pattern used repeatedly:
    #   run_until_complete(asyncio.sleep(0.3))
    #   run_until_complete(asyncio.sleep(0.5))
    sleep_wait_pattern = re.compile(r"run_until_complete\(\s*asyncio\.sleep\(\s*0\.[35]\s*\)\s*\)")
    assert (
        sleep_wait_pattern.search(source) is None
    ), (
        "Expected the mexc exchange tests to eliminate arbitrary waits like "
        "'run_until_complete(asyncio.sleep(0.3/0.5))' in favor of event-driven/timeout helpers, "
        "but such a sleep-based wait is still present."
    )