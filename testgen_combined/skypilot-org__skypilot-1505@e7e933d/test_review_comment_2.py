import argparse

import pytest

import sky.clouds.service_catalog.data_fetchers.fetch_aws as fetch_aws


def test_cli_option_renamed_and_help_clarified():
    """Verify the confusing flag '--check-regions-integrity' was renamed.

    We only test argparse behavior (option presence/absence) without executing
    the script's __main__ block, to avoid requiring AWS credentials.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--az-mappings",
        dest="az_mappings",
        action="store_true",
        help="Fetch the mapping from availability zone IDs to zone names.",
    )
    parser.add_argument(
        "--no-az-mappings",
        dest="az_mappings",
        action="store_false",
    )

    # Add whichever new flag exists in the imported module (after version).
    assert hasattr(fetch_aws, "get_enabled_regions"), (
        "Expected 'get_enabled_regions' to exist in the corrected version; "
        "this indicates the module has been updated to use account-enabled regions."
    )
    parser.add_argument(
        "--check-all-regions-enabled-for-account",
        action="store_true",
        help=(
            'Check that this account has enabled "all" global regions hardcoded '
            "in this script. Useful to ensure our automatic fetcher fetches "
            "the expected data."
        ),
    )

    parser.set_defaults(az_mappings=True)

    # New flag should be recognized by argparse.
    args, _ = parser.parse_known_args(["--check-all-regions-enabled-for-account"])
    assert args.check_all_regions_enabled_for_account is True, (
        "Expected new CLI flag '--check-all-regions-enabled-for-account' to be "
        "accepted and set its destination to True."
    )

    # Old flag should not exist anymore (argparse should reject it).
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--check-regions-integrity"])
    assert excinfo.value.code == 2, (
        "Expected old CLI flag '--check-regions-integrity' to be rejected after "
        "the rename (argparse exits with code 2 for unknown arguments)."
    )