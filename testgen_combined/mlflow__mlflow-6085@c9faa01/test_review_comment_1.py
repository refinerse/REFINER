import warnings

# This warning can be raised during initial conftest loading (before tests run),
# which would fail the test session if not filtered here.
warnings.filterwarnings("ignore", category=Warning, message=r".*PytestRemovedIn9Warning.*")


def test_mlflowclient_import_is_grouped_with_other_mlflow_imports():
    """
    Enforce the import grouping/order in /workspace/mlflow/utils/autologging_utils/client.py.

    Correct ("after") order is:
      entities -> exceptions -> tracking.client (MlflowClient) -> utils -> utils.validation

    The incorrect ("before") version places MlflowClient after the utils.validation block.
    """
    path = "/workspace/mlflow/utils/autologging_utils/client.py"
    source = open(path).read()

    idx_entities = source.find("from mlflow.entities import Param, RunTag, Metric")
    idx_exceptions = source.find("from mlflow.exceptions import MlflowException")
    idx_mlflowclient = source.find("from mlflow.tracking.client import MlflowClient")
    idx_utils = source.find("from mlflow.utils import chunk_list, _truncate_dict")
    idx_validation = source.find("from mlflow.utils.validation import (")

    assert idx_entities != -1, "Expected mlflow.entities import to exist in client.py"
    assert idx_exceptions != -1, "Expected mlflow.exceptions import to exist in client.py"
    assert idx_mlflowclient != -1, "Expected MlflowClient import to exist in client.py"
    assert idx_utils != -1, "Expected mlflow.utils import to exist in client.py"
    assert idx_validation != -1, "Expected mlflow.utils.validation import block to exist in client.py"

    assert idx_entities < idx_exceptions < idx_mlflowclient < idx_utils < idx_validation, (
        "Import order in client.py does not match the expected grouping.\n"
        "Expected:\n"
        "  from mlflow.entities ...\n"
        "  from mlflow.exceptions ...\n"
        "  from mlflow.tracking.client import MlflowClient\n"
        "  from mlflow.utils ...\n"
        "  from mlflow.utils.validation import (...)\n"
        "This should fail if MlflowClient is placed after the validation import block."
    )