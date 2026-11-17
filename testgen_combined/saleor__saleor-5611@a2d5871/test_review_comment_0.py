import re


def test_default_slug_value_is_module_level_constant_and_not_function_arg():
    source = open(
        "/workspace/saleor/warehouse/migrations/0003_warehouse_slug.py",
        encoding="utf-8",
    ).read()

    assert (
        "DEFAULT_SLUG_VALUE" in source
    ), "Expected module-level constant DEFAULT_SLUG_VALUE to be defined."

    assert (
        'DEFAULT_SLUG_VALUE = "warehouse"' in source
    ), 'Expected DEFAULT_SLUG_VALUE to be set to "warehouse" at module level.'

    # The old style used a local variable inside the migration function.
    assert (
        "default_slug_value = " not in source
    ), "Expected no local 'default_slug_value' variable; it should be a module-level constant."

    # The old style passed default slug as an argument to generate_unique_slug.
    m = re.search(r"def\s+generate_unique_slug\s*\(([^)]*)\)\s*:", source)
    assert m, "Expected to find generate_unique_slug() definition."
    params = [p.strip() for p in m.group(1).split(",") if p.strip()]
    assert (
        "default_slug_value" not in params
    ), "generate_unique_slug() should not accept 'default_slug_value'; it should use DEFAULT_SLUG_VALUE."

    assert (
        "generate_unique_slug(warehouse, slug_values, default_slug_value)" not in source
    ), "Expected generate_unique_slug() to be called without passing default_slug_value."

    assert (
        "slugify(instance.name) if instance.name else DEFAULT_SLUG_VALUE" in source
    ), "Expected generate_unique_slug() to use DEFAULT_SLUG_VALUE when instance.name is falsy."