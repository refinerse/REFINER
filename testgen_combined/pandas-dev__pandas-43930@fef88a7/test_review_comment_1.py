import re

import pandas.core.indexes.base  # noqa: F401


def test_base_index_engine_type_annotation_does_not_include_nullable_or_extension_engine():
    """
    The review comment is about the *type information* update for Index._engine_type.

    Before: _engine_type was annotated as a union including NullableEngine/ExtensionEngine.
    After:  _engine_type is annotated as only type[libindex.IndexEngine].

    This has no runtime behavioral impact, so we verify via direct source inspection
    of /workspace/pandas/core/indexes/base.py.
    """
    source = open("/workspace/pandas/core/indexes/base.py", encoding="utf-8").read()

    # Find the annotation line(s) for _engine_type; allow multi-line formatting.
    m = re.search(
        r"(?ms)^\s*_engine_type\s*:\s*(?P<ann>.+?)\s*=\s*libindex\.ObjectEngine\s*$",
        source,
    )
    assert m is not None, (
        "Could not locate the '_engine_type: ... = libindex.ObjectEngine' assignment "
        "in /workspace/pandas/core/indexes/base.py; the test expects this attribute "
        "to exist on the base Index class."
    )

    ann = m.group("ann")

    assert "libindex.NullableEngine" not in ann and "libindex.ExtensionEngine" not in ann, (
        "Index._engine_type annotation should not include NullableEngine or "
        "ExtensionEngine. Found annotation:\n"
        f"{ann}"
    )
    assert "type[libindex.IndexEngine]" in ann, (
        "Index._engine_type annotation should include 'type[libindex.IndexEngine]'. "
        "Found annotation:\n"
        f"{ann}"
    )