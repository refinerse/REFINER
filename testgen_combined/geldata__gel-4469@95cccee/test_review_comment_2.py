import re


def test_find_object_by_id_error_message_includes_id_variable():
    source = open("/workspace/edb/edgeql/compiler/casts.py", "r", encoding="utf-8").read()

    # The pre-fix code used a static message that did not include the actual id.
    assert "with this id does not exist" not in source, (
        "Expected the old static error message to be removed. "
        "The error message should include the specific id value."
    )

    # The fixed code should:
    # - iterate using ForQuery with iterator_alias '_id'
    # - use _id in the WHERE clause (Path(ObjectRef('_id')))
    # - build a dynamic error_message using '++' concatenation and casting _id to str
    patterns = [
        r"qlast\.ForQuery\(",                                  # ForQuery exists
        r"iterator_alias\s*=\s*['\"]_id['\"]",                 # alias is _id
        r"right\s*=\s*qlast\.Path\(\s*steps=\[\s*qlast\.ObjectRef\(name=['\"]_id['\"]\)\s*\]\s*\)",  # WHERE uses _id path
        r"error_message\s*=\s*qlast\.BinOp\(",                 # dynamic message constructed
        r"op\s*=\s*['\"]\+\+['\"]",                            # string concatenation present
        r"TypeCast\([^)]*ObjectRef\(name=['\"]_id['\"]\)",     # _id cast to str
        r"with id",                                            # message mentions 'with id'
        r"does not exist",                                     # message indicates non-existence
    ]

    missing = [p for p in patterns if re.search(p, source, flags=re.DOTALL) is None]
    assert not missing, (
        "Expected _find_object_by_id() to build an assert_exists(message=...) "
        "that includes the id value (via iterator alias '_id' and '++' string "
        "concatenation). Missing expected patterns:\n- "
        + "\n- ".join(missing)
    )