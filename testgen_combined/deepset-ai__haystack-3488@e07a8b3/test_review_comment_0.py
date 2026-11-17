import re


def test_parsr_relevant_headlines_uses_slice_reverse_operator():
    source = open("/workspace/haystack/nodes/file_converter/parsr.py", "r", encoding="utf-8").read()

    # Structural expectation from review: use "alien face" reverse slice instead of list(reversed(...))
    assert "relevant_headlines = relevant_headlines[::-1]" in source, (
        "Expected ParsrConverter._convert_table_element to reverse relevant_headlines using the slice reverse "
        "operator (relevant_headlines[::-1]) as per review comment, but that pattern was not found."
    )

    # Guard against the previous implementation still being present.
    assert "relevant_headlines = list(reversed(relevant_headlines))" not in source, (
        "Found legacy reversal code 'list(reversed(relevant_headlines))'. The review requested using the slice "
        "reverse operator instead."
    )

    # Ensure this is applied specifically to relevant_headlines (not some other list).
    assert re.search(r"\brelevant_headlines\s*=\s*relevant_headlines\[\s*::-1\s*\]", source), (
        "Did not find a clear assignment reversing relevant_headlines via slicing. "
        "Expected pattern like: relevant_headlines = relevant_headlines[::-1]"
    )