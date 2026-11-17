import re


def test_opentracing_tags_import_is_aliased_and_used():
    source = open("/workspace/saleor/graphql/middleware.py").read()

    assert (
        "import opentracing.tags as ot_tags" in source
    ), (
        "Expected opentracing tags import to be aliased as 'ot_tags' to avoid "
        "unused-import warnings and make tag usage explicit."
    )

    assert (
        "span.set_tag(ot_tags.COMPONENT, \"graphql\")" in source
        or "span.set_tag(ot_tags.COMPONENT, 'graphql')" in source
    ), (
        "Expected GraphQL tracing span to set COMPONENT tag via the aliased "
        "import: span.set_tag(ot_tags.COMPONENT, 'graphql')."
    )


def test_opentracing_operation_name_is_more_specific_than_only_operation_type():
    source = open("/workspace/saleor/graphql/middleware.py").read()

    # Ensure the operation string includes operation type + parent type + field name.
    assert (
        "f\"{info.operation.operation}.{info.parent_type.name}.{info.field_name}\""
        in source
        or "f'{info.operation.operation}.{info.parent_type.name}.{info.field_name}'"
        in source
    ), (
        "Expected operation name to include operation, parent type, and field name "
        "(e.g. f\"{info.operation.operation}.{info.parent_type.name}.{info.field_name}\") "
        "instead of using only info.operation.operation."
    )

    # And ensure start_active_span uses that computed `operation` variable.
    assert re.search(
        r"start_active_span\(\s*operation_name\s*=\s*operation\s*\)", source
    ), (
        "Expected start_active_span to use the computed operation variable: "
        "start_active_span(operation_name=operation)."
    )