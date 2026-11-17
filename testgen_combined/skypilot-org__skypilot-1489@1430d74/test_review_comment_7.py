import os

from sky.clouds.aws import AWS


def test_aws_check_credentials_requires_static_credentials_when_not_sso(tmp_path):
    """If not using SSO, ~/.aws/credentials must exist, otherwise check_credentials
    should fail.

    Before fix: returns (True, hints) even if credentials file is missing.
    After fix: returns (False, "...~/.aws/credentials does not exist...") if not SSO.
    """
    # Ensure HOME points to a temp dir with no .aws/credentials.
    os.environ["HOME"] = str(tmp_path)
    aws_dir = tmp_path / ".aws"
    aws_dir.mkdir(parents=True, exist_ok=True)

    # Exercise the real method but avoid network/AWS dependency by monkeypatching
    # instance methods directly (no unittest.mock).
    cloud = AWS()

    # Force "identity is not SSO" so static credentials are required.
    cloud._is_current_identity_sso = lambda: False  # type: ignore[method-assign]
    # Avoid boto3/STS calls; in after code check_credentials calls this first.
    cloud.get_current_user_identity = lambda: "dummy-user-id"  # type: ignore[method-assign]

    ok, msg = cloud.check_credentials()

    assert ok is False, (
        "AWS.check_credentials() must fail when not using SSO and "
        "~/.aws/credentials is missing (static credentials required for multi-cloud). "
        f"Got ok={ok}, msg={msg!r}"
    )
    assert msg is not None and "~/.aws/credentials" in msg, (
        "Failure message should mention the missing ~/.aws/credentials file to guide users. "
        f"Got msg={msg!r}"
    )