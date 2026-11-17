import re


def _get_class_block(source: str, class_name: str) -> str:
    m = re.search(
        rf"(?ms)^\s*class\s+{re.escape(class_name)}\b.*?:\s*\n(?P<body>.*?)(?=^\s*class\s|\Z)",
        source,
    )
    assert m is not None, f"Expected class '{class_name}' to exist in /workspace/src/datasets/load.py"
    return m.group("body")


def _get_method_body(class_block: str, method_name: str) -> str:
    """
    Extract a method body from a class block.

    Note: supports return annotations (-> Type) and multi-line signatures.
    """
    m = re.search(
        rf"(?ms)^\s*def\s+{re.escape(method_name)}\s*\(.*?\)\s*(?:->\s*[^:]+)?\s*:\s*\n(?P<body>.*?)(?=^\s*def\s|\Z)",
        class_block,
    )
    assert m is not None, f"Expected method '{method_name}' to exist"
    return m.group("body")


def test_warning_logged_only_in_get_module_not_in_download_method():
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()
    canonical_block = _get_class_block(source, "CanonicalDatasetModuleFactory")

    # After fix: get_module emits the warning (one level up)
    get_module_body = _get_method_body(canonical_block, "get_module")
    assert "logger.warning" in get_module_body, (
        "Expected CanonicalDatasetModuleFactory.get_module() to emit the warning when it falls back to master."
    )

    # Before fix: there was a dedicated download_dataset_script_from_master() that emitted the warning.
    # After fix: it should be removed/merged.
    assert "def download_dataset_script_from_master" not in canonical_block, (
        "download_dataset_script_from_master() should have been removed/merged so the warning isn't logged there."
    )

    # After fix: download_loading_script() should not log warnings (caller responsibility).
    assert "def download_loading_script" in canonical_block, (
        "Expected CanonicalDatasetModuleFactory to have download_loading_script() in the refactored code."
    )
    download_loading_body = _get_method_body(canonical_block, "download_loading_script")
    assert "logger.warning" not in download_loading_body, (
        "download_loading_script() should not emit warnings; its caller (get_module) should."
    )