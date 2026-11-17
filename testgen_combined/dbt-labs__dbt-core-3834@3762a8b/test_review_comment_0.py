# This file is intentionally a plain-Python "test" that does not rely on pytest
# being importable/runnable in this execution environment.
#
# The harness will execute this file; we use simple assertions so the behavior
# differs only between the "before" and "after" versions.

import re


def test_bigquery_snapshot_config_uses_alias_target_project_and_target_dataset():
    path = "/workspace/test/integration/004_simple_snapshot_test/test-check-col-snapshots-bq/snapshot.sql"
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    assert "target_project=" in source, (
        "Expected snapshot config to use BigQuery alias 'target_project=' "
        "(instead of 'target_database=')."
    )
    assert "target_dataset=" in source, (
        "Expected snapshot config to use BigQuery alias 'target_dataset=' "
        "(instead of 'target_schema=')."
    )

    assert re.search(r"\btarget_database\s*=", source) is None, (
        "Did not expect 'target_database=' in this BigQuery snapshot config file; "
        "it should use the alias 'target_project='."
    )
    assert re.search(r"\btarget_schema\s*=", source) is None, (
        "Did not expect 'target_schema=' in this BigQuery snapshot config file; "
        "it should use the alias 'target_dataset='."
    )


if __name__ == "__main__":
    # Run the single test function directly when executed as a script.
    test_bigquery_snapshot_config_uses_alias_target_project_and_target_dataset()