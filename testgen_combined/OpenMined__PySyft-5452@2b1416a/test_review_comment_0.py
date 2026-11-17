import re


def test_range_proto_does_not_use_has_fields_booleans():
    source = open("/workspace/proto/lib/python/range.proto", "r", encoding="utf-8").read()

    # The review change removes manual presence booleans and relies on protobuf presence checks.
    assert "bool has_start" not in source, (
        "range.proto should not define a manual presence flag 'bool has_start'; "
        "protobuf presence should be checked via HasField (or proto3 optional/wrappers as appropriate)."
    )
    assert "bool has_stop" not in source, (
        "range.proto should not define a manual presence flag 'bool has_stop'; "
        "protobuf presence should be checked via HasField (or proto3 optional/wrappers as appropriate)."
    )
    assert "bool has_step" not in source, (
        "range.proto should not define a manual presence flag 'bool has_step'; "
        "protobuf presence should be checked via HasField (or proto3 optional/wrappers as appropriate)."
    )

    # Ensure id field number matches the updated schema (after removing has_* fields).
    # This makes the test reliably fail on the "before" version (id = 7) and pass on the "after" (id = 4).
    assert re.search(r"\bsyft\.core\.common\.UID\s+id\s*=\s*4\s*;", source), (
        "range.proto should define 'syft.core.common.UID id = 4;' after removing has_* fields "
        "(before version had id = 7 due to extra bool fields)."
    )