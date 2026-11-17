def test_hive_generator_float_check_does_not_use_only_kind_true() -> None:
    source = open("/workspace/sqlglot/dialects/hive.py", "r", encoding="utf-8").read()

    assert 'expression.is_type("float")' in source, (
        "Hive.Generator.datatype_sql should use expression.is_type('float') (without only_kind=True) "
        "to match the expected behavior in the updated code."
    )
    assert 'expression.is_type("float", only_kind=True)' not in source, (
        "Hive.Generator.datatype_sql should not require only_kind=True for float checks in the "
        "updated code; only_kind=True would reintroduce the old/incorrect behavior."
    )