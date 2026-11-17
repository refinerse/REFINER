import re


def test_mexc_exchange_tests_do_not_use_fixed_sleep_waits_for_user_stream_processing():
    """
    Ensures the Mexc exchange test suite does not rely on fixed sleeps (e.g. asyncio.sleep(0.3))
    to yield control to the event loop, and instead uses event-based synchronization (resume_test_event.wait()).
    This enforces the review comment requirement to avoid adding fixed time to the test suite.
    """
    source = open("/workspace/test/hummingbot/connector/exchange/mexc/test_mexc_exchange.py").read()

    # The problematic pattern in the "before" version:
    # asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.3))
    fixed_sleep_pattern = re.compile(
        r"run_until_complete\(\s*asyncio\.sleep\(\s*0\.3\s*\)\s*\)"
    )
    assert not fixed_sleep_pattern.search(source), (
        "Test module still contains fixed 0.3s sleep waits like "
        "`run_until_complete(asyncio.sleep(0.3))`. These add unnecessary time to the suite; "
        "replace them with event-based synchronization (e.g. awaiting `self.resume_test_event`)."
    )

    # The expected synchronization mechanism present in the "after" version.
    assert "resume_test_event" in source and ".wait()" in source, (
        "Expected event-based synchronization using `resume_test_event.wait()` (or equivalent) "
        "was not found in the test module."
    )