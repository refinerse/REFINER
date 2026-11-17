def test_linux_platform_check_uses_startswith_linux():
    """
    Verify Spyder uses the codebase-standard Linux check:
        if sys.platform.startswith('linux'):
    and not:
        if sys.platform == 'Linux'
    """
    source = open("/workspace/spyder/dependencies.py", "r", encoding="utf-8").read()

    assert "if sys.platform.startswith('linux'):" in source, (
        "Expected Linux detection to use `if sys.platform.startswith('linux'):` "
        "in /workspace/spyder/dependencies.py"
    )
    assert "if sys.platform == 'Linux':" not in source, (
        "Found `if sys.platform == 'Linux':` in /workspace/spyder/dependencies.py; "
        "it should be replaced with `if sys.platform.startswith('linux'):`"
    )