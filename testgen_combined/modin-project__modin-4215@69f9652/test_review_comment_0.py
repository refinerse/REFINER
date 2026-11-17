import re


def test_datetime_data_column_d_has_four_elements_not_two():
    source = open(
        "/workspace/modin/experimental/core/execution/native/implementations/omnisci_on_native/test/test_dataframe.py",
        "r",
        encoding="utf-8",
    ).read()

    # Ensure the dt.hour test is present (part of the change context)
    assert "def test_dt_hour" in source, "Expected 'test_dt_hour' to exist in TestDateTime"

    # Extract the list passed to pandas.to_datetime for column "d" in TestDateTime.datetime_data
    m = re.search(
        r'"d"\s*:\s*pandas\.to_datetime\(\s*\[(?P<items>.*?)\]\s*\)',
        source,
        flags=re.S,
    )
    assert (
        m is not None
    ), 'Expected TestDateTime.datetime_data to define column "d" using pandas.to_datetime([...])'

    # Count the number of datetime string literals inside that list
    items = m.group("items")
    # We only count string literals to keep the check simple and robust.
    n_items = len(re.findall(r'"\d{4}-\d{2}-\d{2}[^"]*"', items))

    assert n_items == 4, (
        'TestDateTime.datetime_data["d"] must have 4 datetime values to match other columns. '
        f"Found {n_items}. Having only 2 values can make run_and_compare pass silently due to "
        "both pandas and modin failing at DataFrame construction."
    )