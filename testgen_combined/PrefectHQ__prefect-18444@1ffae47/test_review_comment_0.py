import re


def test_custom_headers_setting_is_imported_at_module_level_not_inside_test():
    """
    Regression test for review comment: PREFECT_CLIENT_CUSTOM_HEADERS should be
    imported at module level (since settings are already imported top-level),
    not imported inside an individual test function.

    This test inspects the tests module source to ensure there is no in-function
    import of `PREFECT_CLIENT_CUSTOM_HEADERS` while still requiring that the
    module-level import exists.
    """
    source = open("/workspace/tests/_internal/test_websockets.py", "r", encoding="utf-8").read()

    assert (
        "PREFECT_CLIENT_CUSTOM_HEADERS" in source
    ), "Expected `PREFECT_CLIENT_CUSTOM_HEADERS` to be referenced in the websockets tests."

    assert (
        "from prefect.settings import (\n" in source
        and "PREFECT_CLIENT_CUSTOM_HEADERS" in source
    ), (
        "Expected `PREFECT_CLIENT_CUSTOM_HEADERS` to be imported at module level from "
        "`prefect.settings` (inside the existing parenthesized import block)."
    )

    # Fail if any test function does a local import of PREFECT_CLIENT_CUSTOM_HEADERS
    in_function_import = re.search(
        r"^\s+from prefect\.settings import PREFECT_CLIENT_CUSTOM_HEADERS\s*$",
        source,
        flags=re.MULTILINE,
    )
    assert (
        in_function_import is None
    ), (
        "Found an in-function import `from prefect.settings import PREFECT_CLIENT_CUSTOM_HEADERS`; "
        "it should be imported at module level to match the intended pattern."
    )