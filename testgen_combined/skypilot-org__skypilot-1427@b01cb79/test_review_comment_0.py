import os

import sky.authentication as auth


def test_get_or_generate_keys_does_not_check_private_key_path_is_none():
    # The review comment notes: `private_key_path is None` can't happen.
    # This was fixed by removing that unreachable check. This is not readily
    # observable via runtime behavior (since expanduser() returns a string),
    # so we verify the updated logic via source inspection.
    source = open("/workspace/sky/authentication.py", "r", encoding="utf-8").read()

    assert "private_key_path is None" not in source, (
        "get_or_generate_keys() should not check `private_key_path is None`; "
        "os.path.expanduser() always returns a string, so this condition is "
        "unreachable and should be removed."
    )

    # Additional sanity: function still returns expanded absolute-ish paths.
    private_key_path, public_key_path = auth.get_or_generate_keys()
    assert isinstance(private_key_path, str) and isinstance(public_key_path, str), (
        "get_or_generate_keys() should return (private_key_path, public_key_path) as strings."
    )
    assert private_key_path == os.path.expanduser(auth.PRIVATE_SSH_KEY_PATH), (
        "Private key path returned by get_or_generate_keys() should match expanded PRIVATE_SSH_KEY_PATH."
    )
    assert public_key_path == os.path.expanduser(auth.PUBLIC_SSH_KEY_PATH), (
        "Public key path returned by get_or_generate_keys() should match expanded PUBLIC_SSH_KEY_PATH."
    )