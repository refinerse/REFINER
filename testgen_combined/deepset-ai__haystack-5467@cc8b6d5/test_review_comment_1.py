import re

import pytest


TXT_CONVERTER_PATH = "/workspace/haystack/preview/components/file_converters/txt.py"


def test_numeric_row_threshold_is_parameterized_not_hardcoded():
    """
    Regression test for review comment:
    the "0.4" ratio used to detect numeric rows should not be hard-coded in _is_numeric_row,
    but exposed/parameterized (e.g., via numeric_row_threshold / self.numeric_row_threshold).
    """
    source = open(TXT_CONVERTER_PATH, "r", encoding="utf-8").read()

    # BEFORE: hard-coded threshold in _is_numeric_row:
    # return len(digits) / len(words) > 0.4 and ...
    hardcoded_pattern = r"return\s+len\(digits\)\s*/\s*len\(words\)\s*>\s*0\.4\s+and"
    assert not re.search(
        hardcoded_pattern, source
    ), "Expected numeric row threshold to be parameterized, but found hard-coded '> 0.4' in _is_numeric_row."

    # AFTER: threshold should be configurable, typically via self.numeric_row_threshold
    assert (
        "numeric_row_threshold" in source or "self.numeric_row_threshold" in source
    ), "Expected a configurable 'numeric_row_threshold' (e.g. stored as self.numeric_row_threshold), but it was not found."