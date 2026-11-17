import re


def test_fiftyone_init_does_not_force_db_migration_on_import():
    source = open("/workspace/fiftyone/__init__.py", "r", encoding="utf-8").read()

    assert (
        "_FIFTYONE_FORCE_DB_CONNECT_ON_IMPORT" not in source
    ), (
        "fiftyone/__init__.py should not reference the legacy "
        "_FIFTYONE_FORCE_DB_CONNECT_ON_IMPORT env var; the package should not "
        "attempt to force DB connect/migration during import."
    )

    assert (
        "migrate_database_if_necessary" not in source
    ), (
        "fiftyone/__init__.py should not call migrate_database_if_necessary() on import; "
        "DB migration must not be triggered from the top-level import path."
    )

    # Ensure logging init is still performed on import
    assert re.search(r"\b_fol\.init_logging\(\)", source), (
        "fiftyone/__init__.py should still initialize logging via _fol.init_logging()."
    )