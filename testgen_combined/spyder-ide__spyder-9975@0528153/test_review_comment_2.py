import os

# Work around a known crash in this execution environment where pytest's
# assertion rewriting can fail with:
# TypeError: required field "lineno" missing from alias
# By opting out of rewriting for this test module, we ensure it runs cleanly.
PYTEST_DONT_REWRITE = True


def test_windows_platform_check_uses_os_name_nt():
    path = "/workspace/spyder/dependencies.py"
    assert os.path.exists(path), (
        "Expected Spyder dependencies module at absolute path "
        "/workspace/spyder/dependencies.py"
    )

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    assert "if os.name == 'nt':" in source, (
        "Windows detection should use `if os.name == 'nt':` (os.name-based "
        "check) in /workspace/spyder/dependencies.py, as requested in the "
        "review comment."
    )
    assert "if sys.platform == 'Windows':" not in source, (
        "Windows detection should not compare sys.platform to the literal "
        "'Windows' (this is not how sys.platform reports Windows). Use "
        "`os.name == 'nt'` instead."
    )