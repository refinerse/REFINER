import os

from sky.clouds.aws import AWS


def test_aws_check_credentials_cli_install_message_uses_skypilot_package_name():
    """Ensure AWS.check_credentials shows PyPI-facing install hint.

    The review discussion asks to show `pip install skypilot[aws]` (not
    `pip install .[aws]` / "sky folder") when AWS CLI is missing/broken.
    This is a runtime-visible behavior via the returned error string.
    """
    # Make sure we don't accidentally depend on a user's ~/.aws state.
    # We do not modify user files; we only influence the subprocess call.
    aws_cloud = AWS()

    # Force the "AWS CLI is not installed properly" branch by making PATH empty,
    # so `aws --version` / `aws configure list` cannot be found.
    old_path = os.environ.get("PATH")
    os.environ["PATH"] = ""
    try:
        ok, msg = aws_cloud.check_credentials()
    finally:
        if old_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = old_path

    assert ok is False, (
        "check_credentials() should fail when AWS CLI is not on PATH, "
        "returning (False, <help message>)."
    )
    assert isinstance(msg, str) and msg, (
        "check_credentials() should return a non-empty help message string "
        "when failing due to missing/broken AWS CLI."
    )

    assert "pip install skypilot[aws]" in msg, (
        "Help message for missing/broken AWS CLI should instruct PyPI users to "
        "install via 'pip install skypilot[aws]' (not editable/local installs). "
        f"Got message:\n{msg}"
    )
    assert "pip install .[aws]" not in msg and "sky folder" not in msg, (
        "Help message should not refer to installing from source ('.[aws]') or "
        "mention running commands under the 'sky folder'. "
        f"Got message:\n{msg}"
    )