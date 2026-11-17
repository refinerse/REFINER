import re


def test_review_fix_maximum_length_typo_and_param_name():
    source = open("/workspace/test/nodes/test_preprocessor.py", "r", encoding="utf-8").read()

    # The review comment asks to fix the typo in the asserted log message:
    # "maximum lenght" -> "maximum length"
    assert (
        "maximum length should be 10." in source
    ), "Expected the test to assert the corrected phrase 'maximum length should be 10.' (not 'maximum lenght')."

    assert (
        "maximum lenght should be 10." not in source
    ), "The misspelled phrase 'maximum lenght should be 10.' should not remain in the file."

    # Also verify the parameter rename that occurred alongside this change in the same hunk:
    # max_chars -> max_chars_check
    assert (
        "max_chars_check=10" in source
    ), "Expected PreProcessor to be instantiated with 'max_chars_check=10' (not the old 'max_chars=10')."

    # Ensure we don't have the old parameter in the added test.
    # Use a regex to avoid false positives from other contexts.
    assert not re.search(
        r"PreProcessor\([^)]*\bmax_chars=10\b", source, flags=re.DOTALL
    ), "Did not expect to find 'max_chars=10' passed to PreProcessor; it should be 'max_chars_check=10'."