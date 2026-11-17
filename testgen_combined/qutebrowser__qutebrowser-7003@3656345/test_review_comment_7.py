import re


def test_external_fileselect_download_scenario_waits_and_checks_downloaded_file():
    """Ensure the external fileselector download scenario waits for completion
    and checks the downloaded file exists (as suggested in review).
    """
    path = "/workspace/tests/end2end/features/downloads.feature"
    source = open(path, encoding="utf-8").read()

    # Extract the "Scenario: Select download path" block up to the next Scenario or EOF.
    m = re.search(
        r"(?ms)^[ \t]*Scenario:\s*Select download path\s*\n(.*?)(?=^[ \t]*Scenario:|\Z)",
        source,
    )
    assert m, f"Expected to find 'Scenario: Select download path' in {path}"
    block = m.group(0)

    assert (
        "And I wait until the download is finished" in block
    ), (
        "The 'Select download path' scenario must wait for the download to finish "
        "before asserting on downloaded files."
    )

    assert (
        "Then the downloaded file subdir/download.bin should exist" in block
    ), (
        "The 'Select download path' scenario must assert that the file was downloaded "
        "to the selected subdir (subdir/download.bin)."
    )