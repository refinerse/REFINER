import os
import tempfile

import pytest

import conans.client.rest.remote_credentials as rc


def test_auth_plugin_loader_is_free_function_and_does_not_raise_when_missing():
    """
    Structural requirement from review:
    - auth plugin loading should be a free function that takes the plugin path
    - RemoteCredentials should not store the plugin path nor raise if the plugin file is missing

    Observable behavior difference:
    - BEFORE: RemoteCredentials.auth() calls a method that raises if plugin file doesn't exist.
    - AFTER: RemoteCredentials uses a free function to load plugin and simply returns None if missing.
    """
    with tempfile.TemporaryDirectory() as cache_folder:
        creds = rc.RemoteCredentials(cache_folder=cache_folder, global_conf={})

        class _Remote:
            name = "myremote"

        remote = _Remote()

        # Ensure interactive prompt isn't reached in either version:
        # In AFTER, empty user+password from env should trigger the
        # "Found password in env-var, but not defined user" exception.
        os.environ.pop("CONAN_LOGIN_USERNAME_MYREMOTE", None)
        os.environ.pop("CONAN_LOGIN_USERNAME", None)
        os.environ["CONAN_PASSWORD_MYREMOTE"] = "secret"

        try:
            with pytest.raises(Exception) as excinfo:
                creds.auth(remote)
            msg = str(excinfo.value)

            # In AFTER, missing plugin is NOT an error; we should reach the env-var validation.
            assert "Found password in env-var, but not defined user" in msg, (
                "Auth should not fail due to missing auth plugin file; it should proceed and "
                "fail at env-var validation when only password is provided."
            )
        finally:
            os.environ.pop("CONAN_PASSWORD_MYREMOTE", None)

        # Additional structural observable: the class shouldn't keep a plugin *path* attribute anymore.
        assert not hasattr(creds, "auth_plugin_path"), (
            "RemoteCredentials should not store 'auth_plugin_path' on the instance; "
            "plugin loading should be handled by a free function taking the path as argument."
        )