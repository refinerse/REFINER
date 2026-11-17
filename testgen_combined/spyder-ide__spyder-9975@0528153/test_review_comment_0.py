import re


def test_declare_dependencies_moved_into_report_missing_dependencies():
    source = open("/workspace/spyder/app/mainwindow.py", "r", encoding="utf-8").read()

    # Ensure there is no module-level dependencies.declare_dependencies() call.
    # In the "before" version under review, it exists at module scope and should
    # therefore fail this assertion. In the "after" version, it should be gone.
    module_level_call = re.search(
        r"(?m)^(?!\s)dependencies\.declare_dependencies\(\)\s*$", source
    )
    assert module_level_call is None, (
        "dependencies.declare_dependencies() should not be called at module "
        "import time; it must be moved inside MainWindow.report_missing_dependencies()."
    )

    # Ensure report_missing_dependencies() contains dependencies.declare_dependencies()
    # in its body (with normal method indentation).
    method_has_call = re.search(
        r"(?ms)^\s{4}def\s+report_missing_dependencies\s*\(\s*self\s*\)\s*:\s*\n"
        r"(?:.*\n)*?\s{8}dependencies\.declare_dependencies\(\)\s*$",
        source,
    )
    assert method_has_call is not None, (
        "Expected MainWindow.report_missing_dependencies() to call "
        "dependencies.declare_dependencies() before checking missing dependencies."
    )