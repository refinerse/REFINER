import re


def test_dataset_module_dataclass_renamed_to_datasetmodule():
    """
    Functional intent of review comment:
    Ensure the public result dataclass was renamed from DatasetModuleFactoryResult to DatasetModule.
    Since importing `src.datasets.load` fails in this environment, we verify via source inspection.
    """
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    assert (
        re.search(r"@dataclass\s*\nclass\s+DatasetModule\s*:", source) is not None
    ), "Expected a '@dataclass class DatasetModule:' definition in /workspace/src/datasets/load.py after the rename."

    assert (
        re.search(r"@dataclass\s*\nclass\s+DatasetModuleFactoryResult\s*:", source) is None
    ), (
        "Did not expect the old '@dataclass class DatasetModuleFactoryResult:' to remain after the rename to "
        "'DatasetModule'."
    )