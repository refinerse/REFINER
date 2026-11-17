import re


def test_windows_runtime_fix_contextmanager_was_deleted():
    source = open("/workspace/certbot/tests/util_test.py", "r", encoding="utf-8").read()

    assert "@contextlib.contextmanager" not in source, (
        "The review requested deletion of the Windows runtime workaround context manager. "
        "Expected no '@contextlib.contextmanager' decorator in /workspace/certbot/tests/util_test.py."
    )

    assert "def _fix_windows_runtime" not in source, (
        "The review requested deletion of '_fix_windows_runtime'. "
        "Expected no 'def _fix_windows_runtime' in /workspace/certbot/tests/util_test.py."
    )

    assert "import contextlib" not in source, (
        "After deleting '_fix_windows_runtime', 'contextlib' should no longer be imported in "
        "/workspace/certbot/tests/util_test.py."
    )

    # Extra guard: ensure we didn't just rename it; this checks for the distinctive Windows logic.
    assert not re.search(r"os\.name\s*!=\s*['\"]nt['\"]", source), (
        "The deleted helper contained Windows-specific branching (os.name != 'nt'). "
        "That logic should not remain in /workspace/certbot/tests/util_test.py."
    )