import sys
import importlib
import warnings


def test_setup_warns_softly_only_for_python_310_and_newer():
    """
    After the change, setup.py should:
      - only warn on import for Python >= 3.10
      - use soft language: "may not yet support Python"
    Before the change it warned for Python >= 3.9 and used "does not support Python".
    """
    sys.modules.pop("setup", None)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", RuntimeWarning)
        importlib.import_module("setup")

    runtime_warnings = [x for x in w if issubclass(x.category, RuntimeWarning)]
    emitted_any = bool(runtime_warnings)

    if sys.version_info >= (3, 10):
        assert emitted_any, (
            "Expected importing setup.py to emit a RuntimeWarning on Python >= 3.10 "
            "(soft compatibility warning)."
        )
        msg = str(runtime_warnings[0].message)
        assert "may not yet support Python" in msg, (
            "Expected warning text to use soft language ('may not yet support Python'); "
            f"got: {msg!r}"
        )
        assert "does not support Python" not in msg, (
            "Warning should not state an absolute 'does not support Python'; "
            f"got: {msg!r}"
        )
    elif sys.version_info[:2] == (3, 9):
        assert not emitted_any, (
            "Did not expect a RuntimeWarning on Python 3.9 after the change "
            "(threshold should be >= 3.10)."
        )
    else:
        # For <3.9, neither before nor after should warn; ensure test is well-defined.
        assert not emitted_any, (
            "Did not expect a RuntimeWarning on Python < 3.9 when importing setup.py."
        )