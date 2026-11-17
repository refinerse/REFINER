import dataclasses

import core.dbt.contracts.publication as publication


def test_public_model_uses_public_node_dependencies_field_name():
    """
    Style/API check from review: PublicModel should expose `public_node_dependencies`
    (not the older `public_dependencies`) as the field storing public node deps.
    """
    PublicModel = publication.PublicModel
    field_names = {f.name for f in dataclasses.fields(PublicModel)}

    assert (
        "public_node_dependencies" in field_names
    ), "PublicModel must define a `public_node_dependencies` dataclass field (requested in review)."

    assert (
        "public_dependencies" not in field_names
    ), "PublicModel must not define the legacy `public_dependencies` field; it should be renamed to `public_node_dependencies`."