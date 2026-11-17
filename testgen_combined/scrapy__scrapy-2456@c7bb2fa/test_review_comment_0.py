import re


def test_test_export_indentation_does_not_strip_expected_bytes():
    """
    Style regression test: ensure test_export_indentation compares the full
    expected bytes including leading/trailing newlines, i.e. it does NOT use
    .strip() on the expected value.
    """
    source = open("/workspace/tests/test_feedexport.py", "r", encoding="utf-8").read()

    # Ensure the test method exists (sanity check; keeps failures informative)
    assert "def test_export_indentation" in source, (
        "Expected tests/test_feedexport.py to define test_export_indentation"
    )

    # The review request is specifically to avoid `.strip()` so that newlines are explicit.
    # Before: self.assertEqual(row['expected'].strip(), data)
    # After:  self.assertEqual(row['expected'], data)
    assert "row['expected'].strip()" not in source, (
        "test_export_indentation must not call .strip() on row['expected']; "
        "the test should be explicit about leading/trailing newlines."
    )

    # And ensure we do the direct comparison (to avoid simply removing strip without asserting)
    assert re.search(r"assertEqual\(\s*row\['expected'\]\s*,\s*data\s*\)", source), (
        "Expected test_export_indentation to directly compare row['expected'] to data "
        "without stripping, e.g. self.assertEqual(row['expected'], data)."
    )