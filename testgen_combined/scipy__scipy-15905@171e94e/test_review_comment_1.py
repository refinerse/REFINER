import re


def test_moment_precision_loss_warning_message_spelling_and_context():
    source = open("/workspace/scipy/stats/_stats_py.py", encoding="utf-8").read()

    # Ensure correct spelling and improved explanatory message.
    assert "catastrophic cancellation" in source, (
        "Expected the moment() precision-loss warning to contain the phrase "
        "'catastrophic cancellation' (correct spelling)."
    )
    assert "nearly identical" in source, (
        "Expected the moment() precision-loss warning to include context that "
        "this occurs when the data are nearly identical."
    )

    # Ensure the old misspelling does not exist anymore.
    assert "catastrophc cancellation" not in source, (
        "Found old misspelled phrase 'catastrophc cancellation' in the source; "
        "it should be corrected to 'catastrophic cancellation'."
    )


def test_moment_precision_loss_detection_logic_uses_abs_mean_and_eps_10():
    source = open("/workspace/scipy/stats/_stats_py.py", encoding="utf-8").read()

    # Updated logic should use '* 10' (not '* 1e6')
    assert re.search(
        r"np\.finfo\(\s*a_zero_mean\.dtype\s*\)\.resolution\s*\*\s*10\b", source
    ), (
        "Expected eps computation to scale resolution by 10 (i.e., '* 10'), "
        "as in the updated precision-loss detection."
    )

    # Updated logic divides by absolute value of mean. Match robustly across
    # newlines/spaces and optional parentheses.
    assert re.search(r"/\s*np\.abs\(\s*mean\s*\)", source), (
        "Expected relative difference to be computed by dividing by np.abs(mean) "
        "(i.e., '/ np.abs(mean)') to avoid sign/zero issues."
    )

    # Ensure the old scaling factor isn't present.
    assert "resolution * 1e6" not in source, (
        "Found old eps scaling 'resolution * 1e6' in the source; expected updated "
        "scaling 'resolution * 10'."
    )