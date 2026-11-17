import re


def test_objectchange_table_object_repr_accessor_uses_changed_object():
    """
    Ensure ObjectChangeTable.object_repr overrides the default accessor with
    tables.A('changed_object') (not tables.A('object_repr')), per review comment.
    """
    source = open("/workspace/netbox/extras/tables/tables.py", "r", encoding="utf-8").read()

    # Extract the ObjectChangeTable class body to avoid matching other tables/columns.
    m = re.search(
        r"(?ms)^class\s+ObjectChangeTable\b.*?:\s*(?P<body>.*?)(?=^\s*class\s+\w+\b|\Z)",
        source,
    )
    assert m, "Could not locate ObjectChangeTable definition in /workspace/netbox/extras/tables/tables.py"

    body = m.group("body")

    # Find the accessor configured on the `object_repr = tables.TemplateColumn(...)` field.
    m2 = re.search(
        r"(?ms)^\s*object_repr\s*=\s*tables\.TemplateColumn\(\s*(?P<args>.*?^\s*\))",
        body,
    )
    assert m2, "Could not locate ObjectChangeTable.object_repr = tables.TemplateColumn(...) definition"

    args = m2.group("args")

    assert "accessor=tables.A('changed_object')" in args, (
        "ObjectChangeTable.object_repr must set accessor=tables.A('changed_object') to ensure the table "
        "prefetches the changed object. (Found different/missing accessor in TemplateColumn args.)"
    )

    assert "accessor=tables.A('object_repr')" not in args, (
        "ObjectChangeTable.object_repr accessor must not be tables.A('object_repr'); it should be "
        "tables.A('changed_object') per the review comment."
    )