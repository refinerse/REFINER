import re


def test_v16_changelog_mentions_public_api_not_private_alpha_grid():
    source = open("/workspace/doc/whats_new/v1.6.rst", encoding="utf-8").read()

    # The changelog should not mention private API symbols.
    assert "_coordinate_descent._alpha_grid" not in source, (
        "Changelog entries are intended for scikit-learn users and should not mention "
        "private symbols like '_coordinate_descent._alpha_grid'. The entry should be "
        "rewritten in terms of public estimators such as LassoCV / ElasticNetCV."
    )

    # Ensure the public-facing entry is present and references PR 29442.
    assert (
        ":class:`linear_model.LassoCV`" in source
        and ":class:`linear_model.ElasticNetCV`" in source
        and ":pr:`29442`" in source
    ), (
        "Expected the v1.6 changelog to mention the public estimators "
        "':class:`linear_model.LassoCV`' and ':class:`linear_model.ElasticNetCV`' "
        "and to reference ':pr:`29442`'."
    )

    # Ensure the old PR reference is removed.
    assert ":pr:`23045`" not in source, (
        "Expected ':pr:`23045`' to not be mentioned in the v1.6 changelog entry."
    )

    # The merged changelog credits both contributors; in the 'after' text the first
    # contributor is not wrapped in an explicit ':user:` role, so match flexibly.
    assert re.search(r"John Hopfensperger\s*<s-banach>", source), (
        "Expected the changelog entry for PR 29442 to credit John Hopfensperger "
        "(s-banach)."
    )
    assert re.search(r":user:`Shruti Nath\s*<snath-xoc>`", source), (
        "Expected the changelog entry for PR 29442 to credit "
        "':user:`Shruti Nath <snath-xoc>`'."
    )