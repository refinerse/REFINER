import os


def test_no_backup_copy_of_postgres_keywords_file_committed():
    """Verify the accidental backup file was removed.

    The reviewed file `dialect_postgres_keywords.py~` should not exist in the repo
    (it's typically an editor/backup artifact and not part of the package).
    """
    backup_path = "/workspace/src/sqlfluff/dialects/dialect_postgres_keywords.py~"
    assert not os.path.exists(backup_path), (
        "Backup/editor artifact file should not be committed: "
        f"{backup_path}. Please remove it from the repository."
    )