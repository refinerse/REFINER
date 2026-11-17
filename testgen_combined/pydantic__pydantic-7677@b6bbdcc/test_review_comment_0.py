import re


def test_root_model_extra_field_error_is_emitted_during_field_collection():
    source = open("/workspace/pydantic/mypy.py", "r", encoding="utf-8").read()

    # The "after" version moved the extra-field RootModel error to collect_fields()
    # and actually calls it with a context node (`stmt`).
    assert "def collect_fields" in source, "Expected pydantic/mypy.py to define collect_fields()."

    assert (
        "if is_root_model and lhs.name != 'root':" in source
    ), "Expected RootModel field restriction check in collect_fields(): non-root field should be rejected."

    assert (
        "error_extra_fields_on_root_model(self._api, stmt)" in source
    ), (
        "Expected collect_fields() to emit an error for extra RootModel fields via "
        "error_extra_fields_on_root_model(self._api, stmt). This should fail on the 'before' code where the error "
        "was not emitted (it was only a commented-out placeholder in add_initializer)."
    )

    # Also ensure it's not still a commented-out placeholder (as in the 'before' code).
    assert (
        "# error_extra_fields_on_root_model" not in source
    ), "Did not expect error_extra_fields_on_root_model to be left commented out."

    # Sanity: the error function must accept a Context parameter (api, context)
    assert re.search(
        r"def\s+error_extra_fields_on_root_model\(\s*api:\s*CheckerPluginInterface\s*,\s*context:\s*Context\s*\)\s*->\s*None\s*:",
        source,
    ), "Expected error_extra_fields_on_root_model(api: CheckerPluginInterface, context: Context) signature."