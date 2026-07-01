import pathlib
import re

import pytest

import sky.backends.wheel_utils as wheel_utils


def test_missing_wheel_error_includes_glob_pattern(monkeypatch, tmp_path):
    """When no wheels exist, the error should include the glob pattern used."""
    # Point wheel dir to an empty temp dir to force the "no wheels" path.
    monkeypatch.setattr(wheel_utils, "WHEEL_DIR", pathlib.Path(tmp_path), raising=True)

    # Version-agnostic lookup of the helper function.
    helper = getattr(wheel_utils, "_get_latest_wheel_and_remove_all_others", None)
    if helper is None:
        helper = getattr(wheel_utils, "_get_latest_wheel_and_cleanup", None)
    assert helper is not None, (
        "Expected wheel_utils to define a helper for finding the latest wheel "
        "and cleaning up old ones."
    )

    with pytest.raises(FileNotFoundError) as excinfo:
        helper()

    msg = str(excinfo.value)
    assert "with glob pattern" in msg, (
        "Expected FileNotFoundError to include the wheel glob pattern for debugging "
        "(i.e., contain 'with glob pattern ... under ...'). "
        f"Got: {msg!r}"
    )

    # Also ensure the message contains some glob-like token (* or **/) to make it useful.
    assert re.search(r"\*\*\/|\*", msg), (
        "Expected FileNotFoundError message to contain a glob-like pattern "
        "(e.g., '**/' or '*'). "
        f"Got: {msg!r}"
    )