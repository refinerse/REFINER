import re


def test_chatphoto_get_and_download_makes_precise_assertion_for_both_files():
    """
    The review requested a 'precise assertion' when fetching both small & big files concurrently.

    We enforce that tests/test_chatphoto.py explicitly checks that BOTH the small and big
    file_unique_id were observed (not just 'in (small, big)' per-file).
    """
    source = open("/workspace/tests/test_chatphoto.py", "r", encoding="utf-8").read()

    # Ensure we are looking at the concurrent version (the refactor in the diff hunk),
    # i.e. the test uses asyncio.as_completed over tasks containing both get_file calls.
    assert "asyncio.as_completed(tasks)" in source, (
        "Expected concurrent get_file logic using asyncio.as_completed(tasks) to be present."
    )

    # The 'before' code only did: assert file.file_unique_id in (small, big)
    # The 'after' code additionally records which one was seen and asserts both occurred.
    assert "asserts = []" in source, (
        "Expected collection of observed file types ('asserts = []') to enable a precise "
        "assertion that both small and big files were fetched."
    )
    assert re.search(r'assert\s+"small"\s+in\s+asserts\s+and\s+"big"\s+in\s+asserts', source), (
        "Expected a precise assertion that BOTH 'small' and 'big' file_unique_id results were "
        "observed, e.g. `assert 'small' in asserts and 'big' in asserts`."
    )