import re


def test_root_model_initializer_conditional_kind_and_collect_fields_extra_field_error():
    source = open("/workspace/pydantic/mypy.py", "r", encoding="utf-8").read()

    # "After" legitimately contains the substring "args[0].kind = ARG_POS" as part of a conditional expression.
    # What we must reject is the *unconditional* assignment present in "before":
    #     args[0].kind = ARG_POS
    assert "args[0].kind = ARG_POS\n" not in source, (
        "RootModel __init__ generation must not unconditionally force the first argument to ARG_POS; "
        "it should preserve whether the root parameter is required vs optional (defaulted)."
    )

    assert (
        "args[0].kind = ARG_POS if args[0].kind == ARG_NAMED else ARG_OPT" in source
    ), "Expected RootModel __init__ fix: conditionally set args[0].kind based on whether it was ARG_NAMED."

    # RootModel should reject extra fields during field collection (not silently accept them).
    assert re.search(
        r"def collect_fields\(\s*self,\s*model_config:\s*ModelConfigData,\s*is_root_model:\s*bool\)",
        source,
    ), "collect_fields must accept an is_root_model flag so RootModel-specific field rules can be applied."

    assert "if is_root_model and lhs.name != 'root':" in source, (
        "RootModel should detect non-'root' fields during field collection."
    )
    assert "error_extra_fields_on_root_model(self._api, stmt)" in source, (
        "RootModel extra fields should emit an error via error_extra_fields_on_root_model(...)."
    )