import re


def test_objectchange_object_template_uses_value_get_absolute_url_guard():
    source = open("/workspace/netbox/extras/tables/template_code.py", encoding="utf-8").read()

    # Extract the OBJECTCHANGE_OBJECT template string to avoid matching other constants.
    m = re.search(
        r'OBJECTCHANGE_OBJECT\s*=\s*"""\s*(?P<body>.*?)\s*"""',
        source,
        flags=re.DOTALL,
    )
    assert m, "Expected to find OBJECTCHANGE_OBJECT triple-quoted template in template_code.py"

    body = m.group("body")

    assert "{% if value and value.get_absolute_url %}" in body, (
        "OBJECTCHANGE_OBJECT should guard link rendering with "
        "`{% if value and value.get_absolute_url %}` (review suggestion), "
        "so it links directly to `value.get_absolute_url` when available."
    )

    assert "value.changed_object" not in body, (
        "OBJECTCHANGE_OBJECT should not reference `value.changed_object`; "
        "it should treat `value` itself as the linked object."
    )