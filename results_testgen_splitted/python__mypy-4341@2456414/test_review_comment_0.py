import argparse
import json
import os
import sys

import pytest

import mypy.dmypy as dmypy


def test_do_status_shows_error_details_when_request_returns_error(tmp_path, capsys, monkeypatch) -> None:
    """
    Verify that when the daemon is unresponsive and request('status') returns {'error': ...},
    dmypy status prints some information about the error (not just a generic message),
    even without --verbose.

    This should FAIL on the "before" version (no error details printed) and PASS on the
    "after" version (show_stats(response) runs when 'error' in response).
    """
    # Create a valid status file so do_status gets past read_status()/check_status().
    status_file = tmp_path / "dmypy_status.json"
    sockname = str(tmp_path / "no_such_dmypy_socket.sock")  # connect will fail -> {'error': ...}
    status_file.write_text(json.dumps({"pid": os.getpid(), "sockname": sockname}))

    monkeypatch.setattr(dmypy, "STATUS_FILE", str(status_file))

    args = argparse.Namespace(verbose=False)

    with pytest.raises(SystemExit) as excinfo:
        dmypy.do_status(args)

    captured = capsys.readouterr()
    out, err = captured.out, captured.err

    assert err == "", "do_status() should not write diagnostics to stderr in this scenario."
    assert excinfo.value.code == f"Daemon is stuck; consider {sys.argv[0]} kill", (
        "When the daemon cannot be reached, do_status() should exit with the stuck-daemon "
        "guidance message."
    )

    # Key behavior check: error details (like "error : [Errno ...] ...") should be printed.
    assert "error" in out.lower(), (
        "do_status() should display some information about the underlying failure when the "
        "status request returns an error (e.g., show_stats printing an 'error' field), "
        "even without --verbose."
    )