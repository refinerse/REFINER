import os


def test_cleanup_fixture_swallows_os_remove_errors_via_source_behavior():
    """
    The review fix wrapped os.remove(tmp_excel_file) in try/except inside the autouse fixture `cleanup`.
    Pytest forbids calling fixtures directly, so we validate the behavior by inspecting the file content.

    BEFORE: cleanup fixture calls os.remove(...) unguarded -> no try/except.
    AFTER: cleanup fixture contains "try:" around os.remove and logs error on exception.
    """
    path = "/workspace/tests/core/data/test_write_single_sheet_excel_data_node.py"
    assert os.path.exists(path), f"Expected source file to exist at {path}"

    source = open(path, "r", encoding="utf-8").read()

    assert "def cleanup(" in source, "Expected an autouse fixture named 'cleanup' in the module under review."

    # Key behavioral change: os.remove is now inside a try/except block.
    assert (
        "try:" in source and "os.remove(tmp_excel_file)" in source and "except Exception as e" in source
    ), (
        "Expected cleanup fixture to catch exceptions when deleting tmp_excel_file "
        "(i.e., wrap os.remove(tmp_excel_file) in try/except Exception)."
    )

    # Ensure we are not accidentally passing on the old behavior.
    assert "if os.path.exists(tmp_excel_file):\n        os.remove(tmp_excel_file)" not in source, (
        "Old behavior detected: cleanup fixture still performs an unguarded os.remove(tmp_excel_file)."
    )