import sky.clouds.aws as aws_mod


def test_check_credentials_sso_hint_wording_is_unambiguous():
    """SSO-related hint should be explicit ("AWS SSO is set.").

    This test forces the SSO branch while preventing any network/service-catalog
    side effects (aws_catalog import triggers AWS calls in some environments).
    """
    cloud = aws_mod.AWS()

    # Force the SSO-detected branch in a version-tolerant way.
    if hasattr(cloud, "_is_current_identity_sso"):
        cloud._is_current_identity_sso = lambda: True  # type: ignore[method-assign]
    else:
        cloud._is_sso_identity = lambda: True  # type: ignore[method-assign]

    # Avoid depending on real user filesystem state.
    aws_mod.os.path.isfile = lambda _: False  # type: ignore[assignment]

    # Avoid real AWS/boto3 calls while keeping check_credentials() moving.
    cloud.get_current_user_identity = lambda: "dummy-user-id"  # type: ignore[method-assign]

    # Prevent aws_catalog import inside check_credentials() from triggering
    # any real AWS calls (it may fetch AZ mappings on import).
    aws_mod.__dict__["aws_catalog"] = object()

    ok, hints = cloud.check_credentials()
    assert ok is True, "check_credentials() should succeed when identity lookup succeeds."

    assert isinstance(hints, str) and hints, (
        "check_credentials() should return a non-empty hint string when SSO identity "
        "is detected and static credentials file is missing."
    )

    assert "AWS SSO is set." in hints, (
        'SSO hint should be explicit and unambiguous ("AWS SSO is set."). '
        f"Got hint: {hints!r}"
    )