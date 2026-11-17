import re


def test_max_message_length_uses_good_bad_text_and_unpacking_instead_of_results_indexing():
    source = open("/workspace/tests/test_constants.py", "r", encoding="utf-8").read()

    # Focus on the *max_message_length* test: that's the hunk in the review diff.
    m = re.search(
        r"(?ms)^[ \t]*async def test_max_message_length\s*\([^)]*\):\s*(?P<body>.*?)(?=^[ \t]*(?:async def|def|class)\s|\Z)",
        source,
    )
    assert m, (
        "Expected to find `async def test_max_message_length(...)` in "
        "/workspace/tests/test_constants.py"
    )
    body = m.group("body")

    # The key behavioral/style change in the diff:
    # BEFORE: results = await tasks; assert isinstance(results[1], BadRequest) ...
    # AFTER:  good_text/bad_text variables; good_msg, bad_msg = await tasks; asserts on both
    assert "good_text" in body and "bad_text" in body, (
        "test_max_message_length should define `good_text` and `bad_text` variables "
        "(good/bad payload pattern), not inline string multiplications only."
    )
    assert "good_msg, bad_msg = await tasks" in body, (
        "test_max_message_length should unpack gather() results via "
        "`good_msg, bad_msg = await tasks` (good_msg/bad_msg pattern)."
    )
    assert "assert good_msg.text == good_text" in body, (
        "test_max_message_length should assert that the good request succeeded by checking "
        "`good_msg.text == good_text`."
    )

    # Ensure we are not still using the old results indexing approach.
    assert "results = await tasks" not in body and "results[1]" not in body, (
        "test_max_message_length should not use `results = await tasks` or index access like "
        "`results[1]`; it should use unpacking into `good_msg, bad_msg`."
    )