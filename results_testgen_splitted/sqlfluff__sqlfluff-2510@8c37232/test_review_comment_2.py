import pytest

from sqlfluff.core.dialects import load_raw_dialect


def test_bigquery_date_part_function_names_do_not_include_add_sub_variants():
    """Ensure removed/commented-out (legacy) date-part functions are no longer registered.

    The review comment asked to remove commented-out code. In this case, the
    observable effect is that certain legacy function names (e.g. DATE_ADD,
    TIMESTAMP_SUB) should no longer be present in the BigQuery dialect set
    "date_part_function_name".
    """
    # Load a fresh instance to avoid cross-test/module import side effects.
    bigquery = load_raw_dialect("bigquery")
    names = bigquery.sets("date_part_function_name")

    forbidden = {
        "DATE_ADD",
        "DATE_SUB",
        "DATETIME_ADD",
        "DATETIME_SUB",
        "TIME_ADD",
        "TIME_SUB",
        "TIMESTAMP_ADD",
        "TIMESTAMP_SUB",
    }
    present = forbidden.intersection(names)

    assert not present, (
        "BigQuery dialect should not register legacy date-part function names that were "
        "intended to be removed with the commented-out code cleanup. "
        f"Unexpected names still present: {sorted(present)}"
    )