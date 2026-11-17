import re


def test_load_from_disk_keep_in_memory_uses_arrow_files_size_not_dataset_info_dataset_size():
    source = open("/workspace/src/datasets/arrow_dataset.py", "r", encoding="utf-8").read()

    # The bug: load_from_disk was using dataset_info.dataset_size, which is None for load_from_disk.
    assert (
        "is_small_dataset(dataset_info.dataset_size)" not in source
    ), "Dataset.load_from_disk must not decide keep_in_memory based on dataset_info.dataset_size (None for load_from_disk)."

    # The fix: compute dataset_size from arrow data files using estimate_dataset_size, then pass to is_small_dataset.
    assert (
        "from .utils.file_utils import estimate_dataset_size" in source
    ), "Dataset.load_from_disk should import estimate_dataset_size to compute size from Arrow files."

    assert (
        "dataset_size = estimate_dataset_size" in source
    ), "Dataset.load_from_disk should compute dataset_size using estimate_dataset_size over state['_data_files']."

    assert re.search(
        r"keep_in_memory\s*=\s*keep_in_memory\s*if\s*keep_in_memory\s*is\s*not\s*None\s*else\s*is_small_dataset\(\s*dataset_size\s*\)",
        source,
    ), "Dataset.load_from_disk should call is_small_dataset(dataset_size) (computed from Arrow files), not dataset_info.dataset_size."