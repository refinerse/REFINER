import re


def test_no_debug_import_traceback_inside_exception_handler():
    source = open("/workspace/core/dbt/main.py", "r", encoding="utf-8").read()

    # The review comment indicates a "debugging" line was added and should be removed.
    # Concretely, the "before" code adds an `import traceback` inside the
    # `except BaseException as e:` handler; the "after" code removes that import.
    #
    # We assert that no such import exists inside that exception handler block.
    pattern = r"except\s+BaseException\s+as\s+e:\s*\n\s*import\s+traceback\b"
    assert not re.search(pattern, source), (
        "core/dbt/main.py should not contain a debug-only `import traceback` inside "
        "`except BaseException as e:`; traceback is already imported at module scope."
    )