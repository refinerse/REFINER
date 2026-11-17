import re


def test_from_frame_signature_and_implementation_no_longer_uses_squeeze_param():
    """
    "After" code removed the `squeeze` parameter and now uses
    from_frame(cls, df, sortorder=None, names=None) with ABCDataFrame checking
    and delegates to from_arrays via df.iteritems().

    "Before" code had from_frame(cls, df, squeeze=True) and built a MI from
    tuples with optional squeeze behavior.

    We source-inspect because pandas cannot be imported in this environment.
    """
    source = open("/workspace/pandas/core/indexes/multi.py", encoding="utf-8").read()

    # Extract the from_frame method body for focused assertions
    m = re.search(
        r"(?ms)^\s*@classmethod\s*\n^\s*def from_frame\([^)]*\):\n(?P<body>(?:^\s+.*\n)+?)(?=^\s*(?:@|def )|\Z)",
        source,
    )
    assert m, "Could not locate MultiIndex.from_frame definition in multi.py"
    body = m.group(0)

    assert "def from_frame(cls, df, sortorder=None, names=None):" in body, (
        "Expected updated MultiIndex.from_frame signature to be "
        "(cls, df, sortorder=None, names=None) (i.e. no `squeeze` parameter)."
    )
    assert "squeeze" not in body, (
        "MultiIndex.from_frame should not reference `squeeze` in the updated "
        "implementation."
    )

    assert "ABCDataFrame" in body and "isinstance(df, ABCDataFrame)" in body, (
        "Expected MultiIndex.from_frame to validate df using ABCDataFrame in "
        "the updated implementation."
    )
    assert "df.iteritems()" in body and "return cls.from_arrays" in body, (
        "Expected MultiIndex.from_frame to build the MultiIndex from columns "
        "via df.iteritems() and delegate to cls.from_arrays in the updated "
        "implementation."
    )

    # Ensure old implementation details are gone
    assert "cls.from_tuples(list(df.values)" not in body, (
        "Old from_frame implementation using from_tuples(list(df.values)) "
        "should not be present."
    )
    assert re.search(r"(?m)^\s*if\s+squeeze\s*:", body) is None, (
        "Old from_frame squeeze if/else block should not be present."
    )