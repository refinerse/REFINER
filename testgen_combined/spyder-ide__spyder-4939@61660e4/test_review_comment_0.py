import re


def test_open_file_in_external_explorer_windows_branch_is_elif_not_if():
    # NOTE: Do not import spyder.widgets.explorer (Qt bindings not available).
    source = open("/workspace/spyder/widgets/explorer.py", "r", encoding="utf-8").read()

    # Isolate the function to avoid false positives elsewhere in the file.
    m = re.search(
        r"(?ms)^def open_file_in_external_explorer\(filename\):\n"
        r"(?P<body>.*?)(?=^\s*(?:def|class)\s|\Z)",
        source,
    )
    assert m is not None, (
        "Could not find open_file_in_external_explorer() in "
        "/workspace/spyder/widgets/explorer.py"
    )
    func_src = "def open_file_in_external_explorer(filename):\n" + m.group("body")

    assert "elif os.name == 'nt':" in func_src, (
        "Regression test for OS branching: open_file_in_external_explorer() "
        "must use `elif os.name == 'nt':` (not a second `if`) after the macOS "
        "check, so the Linux `else:` branch is not executed on macOS."
    )