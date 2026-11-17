import re


def test_cython_casting_hook_targets_pxi_in_and_uses_files_regex_not_types():
    """
    The review change ensures the cython-casting pre-commit hook also runs on
    `.pxi.in` files (which identify doesn't classify as `cython`), by using an
    explicit `files: (\.pyx|\.pxi.in)$` selector instead of `types: [cython]`.

    This test inspects `.pre-commit-config.yaml` because it is not importable.
    """
    source = open("/workspace/.pre-commit-config.yaml", encoding="utf-8").read()

    # Extract the local hook block for `id: cython-casting`
    m = re.search(
        r"(?ms)^-   repo:\s*local\s*\n.*?^    hooks:\s*\n(.*?)(?=^\S|\Z)",
        source,
    )
    assert m, "Expected to find the 'repo: local' section in /workspace/.pre-commit-config.yaml"
    local_hooks = m.group(1)

    m2 = re.search(
        r"(?ms)^    -   id:\s*cython-casting\s*\n(.*?)(?=^    -   id:|\Z)",
        local_hooks,
    )
    assert m2, "Expected to find the local hook with id 'cython-casting'"
    hook_block = m2.group(0)

    assert r"files: (\.pyx|\.pxi.in)$" in hook_block, (
        "cython-casting hook should explicitly target both .pyx and .pxi.in files via "
        r"`files: (\.pyx|\.pxi.in)$` so that .pxi.in is included even if identify doesn't "
        "classify it as cython."
    )

    assert "types: [cython]" not in hook_block, (
        "cython-casting hook should not rely on `types: [cython]` because `.pxi.in` "
        "is not recognized as cython by identify; it should use a `files:` regex instead."
    )