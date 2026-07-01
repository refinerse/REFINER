import os
import types

import pytest

from conans.client.rest.remote_credentials import RemoteCredentials, ConanException


def test_missing_auth_plugin_file_is_ignored(tmp_path):
    """
    Review expectation: if user didn't provide an auth plugin file, Conan should do nothing.
    This means RemoteCredentials.auth() must NOT raise just because the plugin file is missing.
    """
    cache_folder = str(tmp_path)

    # Provide minimal credentials.json so RemoteCredentials can be constructed.
    (tmp_path / "credentials.json").write_text('{"credentials": []}', encoding="utf-8")

    # Ensure no plugin file exists in the cache folder (regardless of the exact expected path).
    rc = RemoteCredentials(cache_folder, global_conf={})
    plugin_path = getattr(rc, "auth_plugin_path", None)
    if plugin_path is not None:
        assert not os.path.exists(plugin_path), "Precondition failed: auth plugin file should be absent"

    # Make the call non-interactive by providing env credentials, so the code doesn't prompt.
    os.environ["CONAN_LOGIN_USERNAME"] = "envuser"
    os.environ["CONAN_PASSWORD"] = "envpass"
    try:
        remote = types.SimpleNamespace(name="myremote")

        try:
            user, pwd = rc.auth(remote)
        except ConanException as e:
            raise AssertionError(
                "Missing auth plugin file must be treated as 'not provided' and MUST NOT raise. "
                f"Got ConanException: {e}"
            ) from e

        assert (user, pwd) == ("envuser", "envpass"), (
            "When no plugin is provided, auth() should continue to other mechanisms (env vars here) "
            "and return those credentials."
        )
    finally:
        os.environ.pop("CONAN_LOGIN_USERNAME", None)
        os.environ.pop("CONAN_PASSWORD", None)