import re


def test_site_type_asn_uses_bigint_scalar():
    """
    Ensure SiteType.asn GraphQL field uses BigInt scalar (supports large ASNs)
    rather than the legacy ASNField which errors on large values.
    """
    source = open("/workspace/netbox/dcim/graphql/types.py", "r", encoding="utf-8").read()

    assert "class SiteType" in source, "Expected SiteType to be defined in netbox/dcim/graphql/types.py"
    assert "asn = graphene.Field" in source, "Expected SiteType to define an 'asn' graphene.Field"

    # Must import BigInt scalar from netbox.graphql.scalars
    assert re.search(
        r"^\s*from\s+netbox\.graphql\.scalars\s+import\s+BigInt\s*$",
        source,
        flags=re.MULTILINE,
    ), (
        "SiteType.asn should use the BigInt scalar (from netbox.graphql.scalars import BigInt) "
        "to support large AS Numbers."
    )

    # Must define asn = graphene.Field(BigInt)
    assert re.search(
        r"^\s*asn\s*=\s*graphene\.Field\(\s*BigInt\s*\)\s*$",
        source,
        flags=re.MULTILINE,
    ), (
        "SiteType.asn must be declared as 'asn = graphene.Field(BigInt)' to avoid errors with large ASNs."
    )

    # Ensure we are not still using ASNField
    assert "ASNField" not in source, (
        "ASNField should not be used for SiteType.asn; it can throw errors with large AS Numbers. "
        "Use BigInt instead."
    )