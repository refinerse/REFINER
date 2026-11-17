import pandas as pd
from pandas.io.formats.format import DataFrameFormatter
from pandas.io.formats.html import HTMLFormatter, NotebookFormatter


def test_notebookformatter_does_not_mutate_columns_index_and_formats_header_labels():
    df = pd.DataFrame([[1, 2], [3, 4]], columns=[1.23456, "B"])
    fmt = DataFrameFormatter(df)

    html_fmt = HTMLFormatter(fmt)
    nb_fmt = NotebookFormatter(fmt)

    # Key behavioral change: NotebookFormatter should no longer mutate
    # self.columns in __init__. Instead, it should override a method that
    # provides formatted column header labels.
    assert list(nb_fmt.columns) == list(
        html_fmt.columns
    ), "NotebookFormatter should not mutate self.columns; it should keep the original columns Index."

    # In the fixed code, notebook-specific formatting is done via an override
    # returning Index.format() results (strings).
    col_labels = nb_fmt._get_columns_formatted_values()
    assert all(
        isinstance(x, str) for x in col_labels
    ), "NotebookFormatter should provide formatted column header labels as strings via _get_columns_formatted_values()."

    # Ensure it is actually using Index.format() output (not raw floats / not a
    # custom float-precision mapping in __init__).
    expected = df.columns.format()
    assert list(col_labels) == list(
        expected
    ), "NotebookFormatter should return df.columns.format() for header labels via _get_columns_formatted_values()."