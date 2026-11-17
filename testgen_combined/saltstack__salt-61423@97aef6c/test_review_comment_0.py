import os
import re


def test_test_schedule_uses_get_schedule_config_file_helper_instead_of_fixture_duplication():
    # Prevent pytest from auto-loading external plugins which can import salt and fail
    # due to dependency mismatches in this execution environment.
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1", (
        "This test expects PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 to be set when running pytest, "
        "to avoid auto-loading external plugins which can raise ImportError in this environment."
    )

    source_path = "/workspace/tests/pytests/unit/modules/test_schedule.py"
    assert os.path.exists(source_path), f"Expected file at {source_path}"
    source = open(source_path, encoding="utf-8").read()

    assert "def schedule_config_file" not in source, (
        "Found a 'schedule_config_file' fixture in tests/pytests/unit/modules/test_schedule.py. "
        "That fixture duplicates the logic of schedule._get_schedule_config_file(); per the review "
        "comment, the tests should call schedule._get_schedule_config_file() instead."
    )

    assert (
        "schedule._get_schedule_config_file()" in source
    ), "Expected tests to call schedule._get_schedule_config_file(), but no call was found."

    assert re.search(
        r"\bschedule_config_file\s*=\s*schedule\._get_schedule_config_file\(\)",
        source,
    ), (
        "Expected an assignment like 'schedule_config_file = schedule._get_schedule_config_file()' "
        "so that the helper is actually used to compute the config file path."
    )