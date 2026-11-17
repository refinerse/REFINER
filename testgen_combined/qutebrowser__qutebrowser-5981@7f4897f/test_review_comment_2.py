import re


def test_qt_environ_test_uses_direct_val_assignment_and_no_config_opt_param():
    """Verify the structural refactor in test_environ_settings only.

    We must not forbid `config_stub.set_obj(...)` elsewhere in the file (it's used
    by other tests). We only care about what *test_environ_settings* does.
    """
    source = open("/workspace/tests/unit/config/test_qtargs.py", encoding="utf-8").read()

    # Extract just the body of test_environ_settings (up to the next test def).
    m = re.search(
        r"def test_environ_settings\([^)]*\):(?P<body>.*?)(?:\n\s*def test_|\Z)",
        source,
        flags=re.S,
    )
    assert m is not None, "Expected to find definition of test_environ_settings in the source file."
    body = m.group("body")

    # 1) Key change: direct attribute assignment
    assert "config_stub.val.qt.environ = config_val" in body, (
        "Expected test_environ_settings to set qt.environ via "
        "`config_stub.val.qt.environ = config_val` (per review comment)."
    )

    # 2) Ensure it no longer uses config_opt indirection inside the test.
    assert "config_opt" not in body, (
        "Expected test_environ_settings to not reference `config_opt` anymore, "
        "since it's always qt.environ after the refactor."
    )

    # Also ensure it no longer uses set_obj for qt.environ in that test.
    assert "config_stub.set_obj(" not in body, (
        "Expected test_environ_settings to no longer call `config_stub.set_obj(...)`; "
        "it should assign `config_stub.val.qt.environ` directly."
    )

    # 3) Parametrization signature: should not include the old redundant\arguments
    old_parametrize_pattern = (
        r"@pytest\.mark\.parametrize\(\s*"
        r"['\"]config_opt,\s*config_val,\s*init_val,\s*envvar,\s*expected['\"]"
    )
    assert re.search(old_parametrize_pattern, source) is None, (
        "Expected the old parametrization signature including 'config_opt' to be removed, "
        "since it's always 'qt.environ' anyway."
    )