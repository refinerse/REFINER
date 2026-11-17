import re


def test_copy_helper_function_renamed_and_canonical_factories_use_download_loading_script():
    """
    Functional intent of review comment:
    - Ensure the helper that copies scripts/resources into importable dir is properly named.
    - Ensure canonical dataset/metric factories share the same method name for fetching the script
      (avoid two near-identical methods differing only by dataset=False).
    Since importing fails in this environment, we inspect the source text directly.
    """
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    # 1) The typo'd helper name should be gone, replaced by the corrected one.
    assert (
        "def _copy_script_and_other_resources_in_importable_dir" in source
    ), "Expected helper to be named '_copy_script_and_other_resources_in_importable_dir' (correct spelling)."

    assert (
        "def _copy_script_and_other_resouces_in_importable_dir" not in source
    ), "Did not expect old misspelled helper '_copy_script_and_other_resouces_in_importable_dir' to remain."

    # 2) CanonicalDatasetModuleFactory and CanonicalMetricModuleFactory should both define the same method name
    # for downloading the main script: download_loading_script (not separate download_dataset_script/download_metric_script).
    assert re.search(
        r"class\s+CanonicalDatasetModuleFactory\b[\s\S]*?\n\s+def\s+download_loading_script\s*\(",
        source,
    ), "Expected CanonicalDatasetModuleFactory to define 'download_loading_script(...)'."

    assert re.search(
        r"class\s+CanonicalMetricModuleFactory\b[\s\S]*?\n\s+def\s+download_loading_script\s*\(",
        source,
    ), "Expected CanonicalMetricModuleFactory to define 'download_loading_script(...)' (same name as dataset factory)."

    assert (
        "def download_dataset_script" not in source
    ), "Did not expect legacy 'download_dataset_script' method to remain; should be renamed to 'download_loading_script'."

    assert (
        "def download_metric_script" not in source
    ), "Did not expect legacy 'download_metric_script' method to remain; should be renamed to 'download_loading_script'."