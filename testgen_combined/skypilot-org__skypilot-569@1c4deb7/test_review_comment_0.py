import re


def test_setup_py_uses_simple_mac_version_check_instead_of_version_comparator():
    source = open("/workspace/sky/setup_files/setup.py", "r", encoding="utf-8").read()

    assert (
        "def version_comparator" not in source
    ), "setup.py should not define version_comparator(); the review requested a simpler inline macOS version check."

    assert (
        "mac_major, mac_minor = mac_version.split('.')[:2]" in source
    ), "setup.py should split mac_version into mac_major/mac_minor via mac_version.split('.')[:2] as suggested in the review."

    # Ensure the comparison is done directly on mac_major/mac_minor, not via a helper.
    assert (
        "version_comparator(" not in source
    ), "setup.py should not call version_comparator(); it should compare mac_major/mac_minor directly."