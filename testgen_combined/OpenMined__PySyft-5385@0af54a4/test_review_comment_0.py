import re


def test_load_checks_nested_args_are_strings_instead_of_blind_str_coercion():
    source = open("/workspace/src/syft/lib/__init__.py", "r", encoding="utf-8").read()

    # Key behavior change requested in review:
    # - validate each element (even nested) is a str
    # - if not, emit a specific error instead of silently accepting
    #
    # "After" code does this with: for lib in libs: if isinstance(lib, str): ... else: critical("Pass lib name...")
    assert "Pass lib name as string object" in source, (
        "Expected load() to reject non-string elements (even in nested iterables) with the "
        "message: 'Pass lib name as string object.'"
    )

    assert (
        re.search(r"for\s+lib\s+in\s+libs\s*:\s*\n\s*if\s+isinstance\(lib,\s*str\)\s*:",
                  source)
        is not None
    ), (
        "Expected load() to iterate over libs and check each element is a string via "
        "`if isinstance(lib, str):` before attempting to load."
    )

    # Ensure nested iterables are handled (the fix uses Iterable and flattens when libs[0] isn't str).
    assert "from typing import Iterable" in source, (
        "Expected load() to use typing.Iterable to detect nested iterables (review requested nested handling)."
    )
    assert (
        "if isinstance(libs[0], Iterable)" in source
        or "isinstance(libs[0],Iterable)" in source
    ), "Expected load() to check whether the first argument is an Iterable to support nested inputs."

    # Backward compatibility with keyword lib=... was added in the "after" version.
    assert 'if "lib" in kwargs.keys()' in source, (
        "Expected load() to support backward-compatible calls like syft.load(lib='opacus') "
        "by checking for 'lib' in kwargs."
    )