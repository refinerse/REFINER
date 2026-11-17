def test_ipam_graphql_scalars_py_removed_or_empty():
    """
    The review resolution removed netbox/ipam/graphql/scalars.py entirely (after version),
    whereas the before version contained a trivial ASNField(BigInt) subclass.

    Assert that the file no longer exists. This must fail on the before version
    (file exists) and pass on the after version (file removed).
    """
    path = "/workspace/netbox/ipam/graphql/scalars.py"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = None

    assert (
        content is None
    ), f"Expected {path} to be removed after the change, but it still exists with content:\n{content!r}"