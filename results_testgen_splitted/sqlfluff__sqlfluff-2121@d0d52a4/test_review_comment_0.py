import importlib

import src.sqlfluff.dialects.dialect_redshift as redshift_mod


def test_redshift_dialect_does_not_define_datatypeidentifersegment_override():
    """Structural regression test: Redshift dialect should NOT define DatatypeIdentifierSegment.

    "Before" code adds a @redshift_dialect.segment(replace=True) class
    DatatypeIdentifierSegment, which the review comment requested to remove.
    "After" code removes that class definition.

    We check this by module attribute presence (safe on both versions).
    """
    importlib.reload(redshift_mod)

    assert not hasattr(redshift_mod, "DatatypeIdentifierSegment"), (
        "dialect_redshift.py should not define DatatypeIdentifierSegment; "
        "the review comment requested this incorrect segment override be removed."
    )