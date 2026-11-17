import pytest

from conan.tools.cmake.toolchain.blocks import LinkerScriptsBlock


class _Conf:
    def __init__(self, linker_scripts):
        self._linker_scripts = linker_scripts

    def get(self, key, check_type=None, default=None):
        assert key == "tools.build:linker_scripts"
        return self._linker_scripts


class _Folders:
    # Used by conan.internal.api.install.generators.relativize_path()
    _base_generators = "/workspace"


class _MinimalConanfile:
    """
    Minimal conanfile object with the attributes used by relativize_path() and LinkerScriptsBlock.
    """
    def __init__(self, linker_scripts):
        self.conf = _Conf(linker_scripts)
        self.folders = _Folders()
        # required by conan.internal.api.install.generators.relativize_paths()
        self.generators_folder = "/workspace"


class _MinimalToolchain:
    generator = "Ninja"


def test_linker_scripts_block_keeps_escaped_quotes_for_paths_with_spaces():
    """
    LinkerScriptsBlock must keep quoting around linker script paths (escaped for CMake string)
    to support paths containing spaces.
    """
    conanfile = _MinimalConanfile(linker_scripts=["/some path/with spaces/script.ld"])
    toolchain = _MinimalToolchain()

    block = LinkerScriptsBlock(conanfile, toolchain, name="linker_scripts")
    ctx = block.context()

    assert isinstance(ctx, dict) and "linker_script_flags" in ctx, (
        "LinkerScriptsBlock.context() must return a dict containing 'linker_script_flags' "
        "when tools.build:linker_scripts is provided."
    )

    flags = ctx["linker_script_flags"]

    assert r'-T\"' in flags and flags.count(r'\"') >= 2, (
        "LinkerScriptsBlock must wrap each linker script path in escaped quotes for CMake, "
        r"i.e. produce flags like -T\"/path with spaces/script.ld\". "
        f"Got: {flags!r}"
    )
    assert "/some path/with spaces/script.ld" in flags, (
        "The linker script path must be preserved in the generated flag string. "
        f"Got: {flags!r}"
    )