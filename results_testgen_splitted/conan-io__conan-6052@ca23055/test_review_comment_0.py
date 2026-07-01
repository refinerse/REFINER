import pytest

from conans.errors import ConanException
from conans.model.info import ConanInfo
from conans.model.values import Values
from conans.model.options import OptionsValues


def _make_info_with_compiler_base(base_present: bool) -> ConanInfo:
    """
    Build a minimal ConanInfo instance without going through ConanInfo.create(),
    just enough for base_compatible()/intel_compatible() behavior.
    """
    info = ConanInfo()

    # full_settings is the "original" profile; settings is the mutable one used for package_id
    if base_present:
        # Provide a compiler.base subtree
        full_settings_text = "\n".join(
            [
                "compiler=intel",
                "compiler.version=19",
                "compiler.base=Visual Studio",
                "compiler.base.version=15",
            ]
        )
    else:
        # No compiler.base subtree
        full_settings_text = "\n".join(
            [
                "compiler=Visual Studio",
                "compiler.version=15",
            ]
        )

    info.full_settings = Values.loads(full_settings_text)
    info.settings = info.full_settings.copy()

    # Not relevant for this test, but required attributes in ConanInfo
    info.full_options = OptionsValues.loads("")
    info.options = info.full_options.copy()
    info.full_requires = []
    info.requires = None
    return info


def test_base_compatible_requires_compiler_base_and_raises_if_missing():
    """
    Review requirement: do not silently return when compiler.base is missing.
    Expected behavior after fix: base_compatible() exists and raises ConanException if no base.
    Before fix: intel_compatible() existed and silently returned when no base.
    This test is written to run on both versions:
      - If base_compatible() doesn't exist, it will call intel_compatible() (before).
      - If base_compatible() exists, it will call it (after).
    """
    info = _make_info_with_compiler_base(base_present=False)

    method = getattr(info, "base_compatible", None)
    if method is None:
        # Before code path (method name was intel_compatible and it silently returned)
        info.intel_compatible()
        assert False, (
            "Compatibility transformation must not silently do nothing when "
            "full_settings.compiler.base is missing; expected an error to be raised."
        )
    else:
        # After code path: must raise when compiler.base is missing
        with pytest.raises(
            ConanException,
            match=r"no 'base' sub-setting",
        ):
            info.base_compatible()