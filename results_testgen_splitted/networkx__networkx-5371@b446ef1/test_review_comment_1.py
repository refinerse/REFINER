import networkx.lazy_imports as lazy_imports


def test_lazy_import_missing_module_dunder_access_does_not_crash_on_file():
    missing = "this_module_should_not_exist__nx_lazy_imports_test"
    proxy = lazy_imports.lazy_import(missing)

    # Accessing __file__ should not trigger the lazy ModuleNotFoundError message.
    # It should behave like a normal module attribute lookup: either succeed or
    # raise AttributeError, but it must not crash due to the buggy super().__getattr__
    # call present in the "before" version.
    try:
        _ = proxy.__file__
    except AttributeError as e:
        msg = str(e)
        assert "super" not in msg, (
            "Accessing proxy.__file__ should not crash due to calling "
            "super().__getattr__ (a bug in the DelayedImportErrorModule implementation). "
            f"Got AttributeError: {e}"
        )
    except ModuleNotFoundError as e:
        assert False, (
            "Accessing proxy.__file__ should not raise ModuleNotFoundError; "
            "it is needed for module repr/printing. "
            f"Got ModuleNotFoundError: {e}"
        )