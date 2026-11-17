import re


def test_person_property_is_name_not_first_name():
    source = open("/workspace/tests/schemas/casts.esdl", "r", encoding="utf-8").read()

    # Locate the Person type block.
    m = re.search(r"(?ms)^\s*type\s+Person\s*\{\s*(.*?)^\s*\}\s*$", source)
    assert m is not None, "Expected to find a 'type Person { ... }' block in /workspace/tests/schemas/casts.esdl"

    person_block = m.group(1)

    assert re.search(r"(?m)^\s*property\s+name\s*->\s*str\s*;\s*$", person_block), (
        "Style requirement: 'type Person' should define 'property name -> str;' "
        "(rename 'first_name' to 'name')."
    )
    assert not re.search(r"(?m)^\s*property\s+first_name\s*->\s*str\s*;\s*$", person_block), (
        "Style requirement: 'type Person' must not define 'property first_name -> str;'; "
        "it should be named 'name' instead."
    )