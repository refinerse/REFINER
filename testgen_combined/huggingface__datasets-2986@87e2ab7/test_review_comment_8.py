import re


def test_download_loading_script_renamed_and_from_master_removed():
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    # The review change: method renamed to download_loading_script and the "*_from_master" variant removed/merged.
    assert "def download_loading_script" in source, (
        "Expected Canonical*ModuleFactory to expose 'download_loading_script' after the rename."
    )

    assert "download_dataset_script_from_master" not in source, (
        "Expected 'download_dataset_script_from_master' to be removed after merging the master-fallback logic "
        "into 'download_loading_script' / 'get_module'."
    )
    assert "download_metric_script_from_master" not in source, (
        "Expected 'download_metric_script_from_master' to be removed after merging the master-fallback logic "
        "into 'download_loading_script' / 'get_module'."
    )

    # Ensure the old names are not kept around (avoids regressions/backward-compat leakage inside factories).
    assert not re.search(r"\bdef\s+download_dataset_script\s*\(", source), (
        "Expected the old method name 'download_dataset_script' to be renamed (not still defined)."
    )
    assert not re.search(r"\bdef\s+download_metric_script\s*\(", source), (
        "Expected the old method name 'download_metric_script' to be renamed (not still defined)."
    )