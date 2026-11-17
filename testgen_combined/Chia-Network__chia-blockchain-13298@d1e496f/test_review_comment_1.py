# NOTE: This file intentionally does not import pytest (or anything else outside stdlib),
# because the execution environment's pytest import chain can fail due to dependency issues.

def test_lonely_daemon_uses_snake_case_name():
    source = open("/workspace/tests/core/daemon/test_daemon.py", "r", encoding="utf-8").read()

    assert "lonelyDaemon" not in source, (
        "Found camelCase `lonelyDaemon` in /workspace/tests/core/daemon/test_daemon.py, "
        "but the review requested snake_case `lonely_daemon`."
    )
    assert "lonely_daemon" in source, (
        "Expected snake_case `lonely_daemon` to be present in "
        "/workspace/tests/core/daemon/test_daemon.py after addressing the review."
    )