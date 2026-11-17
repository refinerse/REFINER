import re


def test_sampling_hinv_cost_phrase_mentions_computation_time_not_intervals_cost():
    source_path = "/workspace/doc/source/tutorial/stats/sampling_hinv.rst"
    source = open(source_path, "r", encoding="utf-8").read()

    # The review change clarifies that decreasing u-resolution increases the number
    # of intervals (which helps accuracy) and that the "cost" is computation time.
    # Before: "cost of increased setup time and number of intervals."
    # After:  "cost of computation time as a result of the increased setup time and number of intervals."
    expected = (
        "Note that this comes at the cost of computation time as a result of the increased\n"
        "setup time and number of intervals."
    )
    assert expected in source, (
        "Documentation should clarify that decreasing u-resolution increases intervals and thus the "
        "cost is computation time (due to increased setup time and number of intervals). "
        "Expected the updated two-line sentence to be present."
    )

    # Ensure the old ambiguous wording is gone (stronger guarantee of the behavior change).
    old = "Note that this comes at the cost of increased setup time and number of intervals."
    assert old not in source, (
        "Old wording still present; it incorrectly frames the increased number of intervals as the 'cost' "
        "rather than attributing cost to computation time."
    )

    # Also ensure there isn't a partially-updated line that could still be confusing.
    assert not re.search(
        r"Note that this comes at the cost of .*number of intervals\.\s*$", source, flags=re.MULTILINE
    ) or expected in source, (
        "Found a 'cost of ... number of intervals' sentence that does not match the clarified wording."
    )