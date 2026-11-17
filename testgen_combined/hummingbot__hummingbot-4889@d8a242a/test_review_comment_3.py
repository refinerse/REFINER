import re


def test_mexc_tests_define_and_use_async_run_with_timeout_wrapper():
    source_path = "/workspace/test/hummingbot/connector/exchange/mexc/test_mexc_api_order_book_data_source.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # 1) The helper must exist
    assert "def async_run_with_timeout" in source, (
        "Expected the test class to define async_run_with_timeout() wrapper."
    )

    # 2) The helper must implement the reviewed behavior (wait_for + run_until_complete)
    helper_pattern = (
        r"def\s+async_run_with_timeout\s*\(\s*self\s*,\s*coroutine\s*:\s*Awaitable\s*,\s*timeout\s*:\s*float\s*=\s*1\s*\)\s*:"
        r"[\s\S]*?"
        r"run_until_complete\(\s*asyncio\.wait_for\(\s*coroutine\s*,\s*timeout\s*\)\s*\)"
    )
    assert re.search(helper_pattern, source), (
        "Expected async_run_with_timeout(self, coroutine: Awaitable, timeout: float = 1) to call "
        "self.ev_loop.run_until_complete(asyncio.wait_for(coroutine, timeout))."
    )

    # 3) All run_until_complete usages should be inside the helper, not in tests directly.
    #    Count occurrences: in the fixed version it should appear exactly once (inside helper).
    occurrences = len(re.findall(r"\brun_until_complete\b", source))
    assert occurrences == 1, (
        f"Expected exactly one 'run_until_complete' usage (inside async_run_with_timeout only), "
        f"but found {occurrences}. This indicates tests are still calling run_until_complete directly."
    )

    # 4) And tests should actually use the wrapper at least once
    assert "self.async_run_with_timeout(" in source, (
        "Expected tests to use self.async_run_with_timeout(...) instead of calling run_until_complete directly."
    )