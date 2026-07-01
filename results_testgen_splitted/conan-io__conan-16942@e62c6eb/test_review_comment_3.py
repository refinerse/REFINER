import os
import textwrap

import pytest

from conans.client.rest.remote_credentials import RemoteCredentials
from conan.internal.cache.home_paths import HomePaths


class _DummyGlobalConf:
    def get(self, *_args, **_kwargs):
        return False


class _Remote:
    def __init__(self, name, url):
        self.name = name
        self.url = url


def test_auth_remote_plugin_receives_remote_object_and_can_use_url(tmp_path):
    """
    The auth plugin should receive the full Remote object (not just remote.name),
    so it can use attributes like remote.url to decide credentials.
    This fails in the "before" implementation because it loads 'auth.py' expecting
    'auth_plugin', not 'auth_remote.py' with 'auth_remote_plugin'.
    """
    cache_folder = str(tmp_path)

    # Ensure credentials.json doesn't exist so we don't accidentally succeed via cache.
    creds_path = os.path.join(cache_folder, "credentials.json")
    assert not os.path.exists(creds_path), "Precondition failed: credentials.json must not exist"

    # Provide auth_remote.py plugin in the expected location.
    # After code loads it and calls auth_remote_plugin(remote, user=user)
    # Before code ignores it and tries to load auth.py instead (and raises).
    auth_remote_plugin_path = HomePaths(cache_folder).auth_remote_plugin_path
    os.makedirs(os.path.dirname(auth_remote_plugin_path), exist_ok=True)
    with open(auth_remote_plugin_path, "w", encoding="utf-8") as f:
        f.write(
            textwrap.dedent(
                """
                def auth_remote_plugin(remote, user=None):
                    # Prove we received the full Remote object by using remote.url
                    if remote.url == "https://example.test":
                        return "user_from_url", "pass_from_url"
                    return None, None
                """
            ).lstrip()
        )

    rc = RemoteCredentials(cache_folder, _DummyGlobalConf())
    remote = _Remote(name="myremote", url="https://example.test")

    try:
        user, password = rc.auth(remote)
    except Exception as e:
        assert False, (
            "Auth should be resolved via 'auth_remote.py' plugin using remote.url, "
            f"but an exception was raised instead: {type(e).__name__}: {e}"
        )

    assert (user, password) == ("user_from_url", "pass_from_url"), (
        "Expected credentials to come from auth_remote.py plugin based on remote.url, "
        f"but got {(user, password)}"
    )