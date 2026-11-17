import os


def test_public_interface_does_not_force_db_connect_env_var_hook():
    source_path = "/workspace/fiftyone/__public__.py"
    assert os.path.exists(source_path), f"Expected file to exist: {source_path}"

    source = open(source_path, "r", encoding="utf-8").read()

    assert (
        "_FIFTYONE_FORCE_DB_CONNECT_ON_IMPORT" not in source
    ), (
        "fiftyone/__public__.py should not contain the legacy env-var hook "
        "('_FIFTYONE_FORCE_DB_CONNECT_ON_IMPORT') that triggers database "
        "connection on import. The public interface should not conditionally "
        "establish DB connections during import."
    )