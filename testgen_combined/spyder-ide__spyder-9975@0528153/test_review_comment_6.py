import os

# Work around third-party pytest plugins in the execution environment that
# can crash pytest during collection on Python 3.11.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


def test_pympler_features_text_is_shortened_per_style_review_comment():
    """
    Importing spyder.dependencies is not possible in this environment, so we
    verify the requested style change via source inspection.
    """
    source = open("/workspace/spyder/dependencies.py", encoding="utf-8").read()

    expected = "Tool to measure the memory behavior of Python objects"
    assert expected in source, (
        "Expected the 'pympler' dependency features description to be updated to "
        f"'{expected}'."
    )

    old = (
        "Development tool to measure, monitor and analyze the memory behavior "
        "of Python objects in a running Python application."
    )
    assert old not in source, (
        "Found the old verbose 'pympler' features description; it should be "
        "replaced by the shorter sentence requested in the review."
    )