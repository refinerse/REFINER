import re


def test_dependencies_declare_dependencies_moved_into_report_missing_dependencies_and_removed_from_module_level():
    source_path = "/workspace/spyder/app/mainwindow.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    # 1. Ensure the old module-level call was removed.
    module_level_pattern = re.compile(
        r"#\s*={3,}\s*\n"
        r"#\s*Dependencies\s*\n"
        r"#\s*={3,}\s*\n"
        r"\s*dependencies\.declare_dependencies\(\)\s*\n",
        flags=re.MULTILINE,
    )
    assert not module_level_pattern.search(source), (
        "Found a module-level call to dependencies.declare_dependencies() under "
        "the 'Dependencies' header. It should have been removed from module "
        "scope and relocated to where it's actually needed."
    )

    # 2. Ensure it's called inside report_missing_dependencies().
    # Capture just the function body by slicing from its def line to the next
    # top-level def (same indent) or end of file.
    m = re.search(
        r"(?m)^(?P<indent>[ \t]*)def report_missing_dependencies\(self\):[ \t]*\n",
        source,
    )
    assert m is not None, (
        "Could not find the definition of report_missing_dependencies(self) "
        "in /workspace/spyder/app/mainwindow.py."
    )
    indent = m.group("indent")
    start = m.start()

    # Find next function definition with the same indentation (i.e. next method)
    next_def = re.search(
        r"(?m)^" + re.escape(indent) + r"def [A-Za-z_][A-Za-z0-9_]*\(",
        source[m.end():],
    )
    end = (m.end() + next_def.start()) if next_def else len(source)

    func_block = source[start:end]

    assert "dependencies.declare_dependencies()" in func_block, (
        "Expected dependencies.declare_dependencies() to be called inside "
        "report_missing_dependencies(), so dependency declaration happens only "
        "when missing dependencies are being checked/reported."
    )