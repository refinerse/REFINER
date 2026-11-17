import re


def test_whatsnew_0202_drop_empty_list_entry_wording():
    source = open("/workspace/doc/source/whatsnew/v0.20.2.txt", encoding="utf-8").read()

    expected_line = "- Bug in ``pd.drop([])`` for DataFrame with non-unique indices (:issue:`16270`)"
    assert (
        expected_line in source
    ), f"Expected whatsnew entry to match review comment wording exactly:\n{expected_line}\n\nFound relevant line(s):\n" + "\n".join(
        line for line in source.splitlines() if "drop([])" in line and "16270" in line
    )

    # Ensure the old, incorrect phrasing is not present (helps catch regressions/duplicates).
    old_line_pattern = re.compile(
        r"-\s*Fix\s+``pd\.drop\(\[\]\)``\s+for\s+dataframes\s+with\s+non-unique\s+indices\s+\(:issue:`16270`\)",
        flags=re.IGNORECASE,
    )
    assert not old_line_pattern.search(
        source
    ), "Old whatsnew entry phrasing ('Fix pd.drop([]) for dataframes...') should not be present."