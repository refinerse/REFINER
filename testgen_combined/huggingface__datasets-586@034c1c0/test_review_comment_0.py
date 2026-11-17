import types

import pytest

import datasets.text.text as text_module


def test_text_split_generators_raises_valueerror_when_data_files_missing():
    """
    Regression test for review comment: argument validation must not use `assert`.
    When config.data_files is falsy, _split_generators should raise ValueError
    with a helpful message (so it's not skipped under Python -O).
    """
    Text = text_module.Text

    # Avoid instantiating Text() since Builder __init__ tries to create cache lock files.
    # We only need an object that provides `.config.data_files`.
    builder = object.__new__(Text)
    builder.config = types.SimpleNamespace(data_files=None)

    class DummyDLManager:
        def download_and_extract(self, data_files):
            raise AssertionError(
                "download_and_extract must not be called when data_files is missing; "
                "the code should fail fast with ValueError."
            )

    try:
        builder._split_generators(DummyDLManager())
        pytest.fail(
            "Expected a ValueError when config.data_files is missing. "
            "If this didn't raise, the code is not validating inputs properly."
        )
    except Exception as e:
        assert isinstance(
            e, ValueError
        ), f"Expected ValueError (not assert-based validation). Got {type(e).__name__}: {e}"
        assert "At least one data file must be specified" in str(
            e
        ), "ValueError message should explain that at least one data file must be specified."
        assert "data_files=" in str(
            e
        ), "ValueError message should include the data_files value for debugging."