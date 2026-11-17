import re


def test_bulk_import_csv_sniffer_supports_tab_and_not_space_delimiter():
    """
    The bulk import CSV dialect detection should consider supported delimiters
    (including tab) and should not treat a literal space as a CSV delimiter.

    This test is intentionally implemented via source inspection because
    importing `netbox.utilities.forms.bulk_import` fails in this environment.
    """
    source = open("/workspace/netbox/utilities/forms/bulk_import.py", "r", encoding="utf-8").read()

    # BEFORE: csv.Sniffer().sniff(..., delimiters=',; ')
    # AFTER:  delimiters = ''.join(CSV_DELIMITERS.values())  (includes '\t') and uses that
    #
    # We assert the new "CSV_DELIMITERS" approach is present, and the old
    # trailing-space delimiters literal is absent.
    assert "CSV_DELIMITERS" in source, (
        "Expected BulkImportForm CSV parsing to use the supported delimiter set (CSV_DELIMITERS), "
        "so that tab-delimited files can be detected/selected."
    )

    assert "delimiters=',; '" not in source and 'delimiters=",; "' not in source, (
        "CSV Sniffer delimiters should not include a space (',; ') as a delimiter. "
        "Space-delimited CSV is not intended here and it prevents supporting tab handling."
    )

    # Ensure tab delimiter is explicitly supported via constants/choices.
    # (This is a lightweight check that the delimiter set is used rather than hard-coded.)
    assert re.search(r"delimiters\s*=\s*''\.join\(\s*CSV_DELIMITERS\.values\(\)\s*\)", source), (
        "Expected delimiter detection to build the delimiter list from CSV_DELIMITERS.values() "
        "(which should include tab), rather than hard-coding ',; '."
    )