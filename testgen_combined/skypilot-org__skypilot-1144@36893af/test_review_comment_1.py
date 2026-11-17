import pathlib

import pytest

import sky.backends.wheel_utils as wheel_utils


def test_cleanup_does_not_unlink_non_symlink_files(monkeypatch, tmp_path):
    """
    The review fix removed behavior that unlinked non-directory entries in WHEEL_DIR.

    Before: cleanup iterates WHEEL_DIR and for any entry other than the latest wheel's
    parent dir, it unlinks it (including regular files like ".tmp" etc.).
    After: cleanup only removes old *directories*; it must not unlink regular files.

    This test creates:
      - two wheel hash directories each containing a wheel file
      - an extra regular file at WHEEL_DIR/.sentinel that must survive cleanup
    """
    wheels_dir = tmp_path / "wheels"
    wheels_dir.mkdir()

    old_hash_dir = wheels_dir / "oldhash"
    new_hash_dir = wheels_dir / "newhash"
    old_hash_dir.mkdir()
    new_hash_dir.mkdir()

    wheel_filename = (
        f"{wheel_utils._PACKAGE_WHEEL_NAME}-"
        f"{wheel_utils.version.parse(wheel_utils.sky.__version__)}-"
        "py3-none-any.whl"
    )
    (old_hash_dir / wheel_filename).write_text("old")
    (new_hash_dir / wheel_filename).write_text("new")

    sentinel = wheels_dir / ".sentinel"
    sentinel.write_text("do not delete")

    # Ensure module uses our temp wheel dir.
    monkeypatch.setattr(wheel_utils, "WHEEL_DIR", wheels_dir)

    # Call the internal cleanup helper (name differs before/after).
    if hasattr(wheel_utils, "_get_latest_wheel_and_cleanup"):
        latest = wheel_utils._get_latest_wheel_and_cleanup()
    else:
        latest = wheel_utils._get_latest_wheel_and_remove_all_others()

    assert latest.exists(), "Sanity check: cleanup should return an existing wheel path."

    assert sentinel.exists(), (
        "Cleanup must not unlink regular files in WHEEL_DIR (only remove old wheel "
        "directories). The old implementation deleted non-directory entries."
    )