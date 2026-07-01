import pytest

import networkx.lazy_imports as lazy


def test_lazy_import_missing_module_reports_original_callsite_in_error_message():
    def make_proxy():
        # This is the callsite we expect the lazy error to report.
        proxy = lazy.lazy_import("module_that_does_not_exist_anywhere_12345")
        return proxy

    proxy = make_proxy()

    with pytest.raises(ModuleNotFoundError) as excinfo:
        # Trigger the deferred error by accessing an attribute.
        proxy.some_attribute

    msg = str(excinfo.value)

    assert (
        "This error is lazily reported" in msg
    ), f"Expected lazy-import error message to indicate deferred reporting; got:\n{msg}"

    assert (
        "having originally occured in" in msg
    ), f"Expected lazy-import error message to include original callsite header; got:\n{msg}"

    assert (
        "in make_proxy" in msg
    ), f"Expected lazy-import error message to include original calling function name; got:\n{msg}"

    assert (
        "proxy = lazy.lazy_import(" in msg
    ), f"Expected lazy-import error message to include the original source line context; got:\n{msg}"