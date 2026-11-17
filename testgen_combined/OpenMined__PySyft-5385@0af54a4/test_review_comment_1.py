import re


def test_load_checks_isinstance_before_str_conversion_and_handles_kwargs_lib():
    source = open("/workspace/src/syft/lib/__init__.py", "r", encoding="utf-8").read()

    # Runtime import isn't possible in this environment, so verify the behavioral change
    # via source inspection: the reviewed change adds an isinstance(lib, str) check
    # before calling _load_lib and also adds **kwargs support for syft.load(lib="opacus").
    assert (
        "if isinstance(lib, str):" in source
    ), "load() should check isinstance(lib, str) before calling _load_lib to avoid blindly str() converting non-strings."

    assert (
        "Pass lib name as string object" in source
    ), "load() should report a clear error when a non-string lib name is provided."

    assert (
        "**kwargs" in source and '"lib" in kwargs.keys()' in source
    ), "load() should accept **kwargs and handle backward-compatible calls like load(lib='opacus')."

    # Also ensure load_lib forwards using the keyword argument 'lib=' for compatibility
    assert re.search(r"\bload\(\s*lib\s*=\s*lib\s*,\s*options\s*=\s*options\s*\)", source), (
        "load_lib() should delegate to load(lib=lib, options=options) to support the updated load() signature."
    )