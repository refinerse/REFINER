import os


# This must be set before importing pytest so that pytest doesn't auto-load
# external plugins that may emit fatal warnings during initialization.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

import re


def test_databricks_models_artifact_repo_uses_direct_mlflowclient_import():
    source_path = "/workspace/mlflow/store/artifact/databricks_models_artifact_repo.py"
    source = open(source_path, "r", encoding="utf-8").read()

    assert "from mlflow.tracking.client import MlflowClient" in source, (
        "Expected DatabricksModelsArtifactRepository to import MlflowClient directly with "
        "`from mlflow.tracking.client import MlflowClient` (as in the reverted/correct version)."
    )

    assert re.search(r"\bclient\s*=\s*MlflowClient\s*\(\s*registry_uri\s*=", source), (
        "Expected client construction to use the directly imported class, e.g. "
        "`client = MlflowClient(registry_uri=...)`."
    )

    assert "mlflow.tracking.MlflowClient" not in source, (
        "Did not expect `mlflow.tracking.MlflowClient` usage in this module; it should use the "
        "directly imported `MlflowClient` instead."
    )