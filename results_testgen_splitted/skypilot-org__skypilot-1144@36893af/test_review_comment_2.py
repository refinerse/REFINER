import os
import pathlib
import tempfile

import pytest

import sky
import sky.backends.wheel_utils as wheel_utils


def test_build_sky_wheel_raises_runtimeerror_if_no_wheel_generated(monkeypatch):
    """If pip wheel succeeds but no wheel file is produced, we should raise.

    This is the behavior change from the review comment: add a RuntimeError
    "just in case the glob fails" when searching for the built wheel.
    """
    # Ensure we never touch the user's real ~/.sky/wheels. Point WHEEL_DIR to a
    # temp directory and keep internal constants consistent.
    tmp_root = pathlib.Path(tempfile.mkdtemp(prefix="skypilot_wheel_utils_test_"))
    monkeypatch.setattr(wheel_utils, "WHEEL_DIR", tmp_root / "wheels", raising=True)
    monkeypatch.setattr(
        wheel_utils, "_WHEEL_LOCK_PATH", wheel_utils.WHEEL_DIR.parent / ".wheels_lock", raising=True
    )

    # Make the source tree look "unchanged" so build_sky_wheel() won't try to
    # rebuild based on modification times; instead it will go straight to
    # choosing the latest wheel.
    monkeypatch.setattr(wheel_utils, "SKY_PACKAGE_PATH", tmp_root / "fake_sky_pkg", raising=True)
    wheel_utils.SKY_PACKAGE_PATH.mkdir(parents=True, exist_ok=True)

    # Ensure build_sky_wheel() decides to (re)build by making SKY_PACKAGE_PATH
    # appear newer than WHEEL_DIR.
    monkeypatch.setattr(wheel_utils.os.path, "getmtime", lambda p: 100.0, raising=True)
    monkeypatch.setattr(wheel_utils.os, "walk", lambda p: [(str(p), [], ["x.py"])], raising=True)

    # Avoid copying/symlinking real setup files. Make 'setup_files' empty.
    setup_files = wheel_utils.SKY_PACKAGE_PATH / "setup_files"
    setup_files.mkdir(parents=True, exist_ok=True)

    # Critical: simulate "pip wheel" succeeding but producing no wheel file in tmp_dir.
    def _fake_run(*args, **kwargs):
        return None

    monkeypatch.setattr(wheel_utils.subprocess, "run", _fake_run, raising=True)

    # The before code uses `next(tmp_dir.glob(wheel_name))` which raises StopIteration
    # (or later FileNotFoundError from cleanup) and is not converted to RuntimeError.
    # The after code catches StopIteration and raises RuntimeError.
    with pytest.raises(
        RuntimeError,
        match=r"No wheel file is generated",
    ):
        wheel_utils.build_sky_wheel()

    assert True, (
        "Expected build_sky_wheel() to raise RuntimeError with a clear message "
        "when the wheel glob finds no generated wheel file."
    )