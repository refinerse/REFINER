import pytest

import haystack.components.converters.docx as docx_mod


def test_docx_table_format_enum_is_component_specific_name():
    """
    The table format enum is intended for this DOCX converter component, so it should be named
    `DOCXTableFormat` (not the generic `TableFormat`).
    """
    assert hasattr(
        docx_mod, "DOCXTableFormat"
    ), "Expected a DOCX-specific enum name `DOCXTableFormat` to exist in haystack.components.converters.docx"

    assert not hasattr(
        docx_mod, "TableFormat"
    ), "Did not expect a generic enum name `TableFormat` in haystack.components.converters.docx; use `DOCXTableFormat` instead"