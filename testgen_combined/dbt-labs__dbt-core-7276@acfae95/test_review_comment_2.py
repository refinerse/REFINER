import pytest


def test_projectdependencies_naming_is_used_in_publication_contracts():
    """
    Style regression test: the review requested renaming the container type to
    `ProjectDependencies` (and related `ProjectDependency`) instead of the prior
    `Dependencies`/`DependentProjects` names.

    This is observable at runtime via module attributes.
    """
    import core.dbt.contracts.publication as pub

    assert hasattr(
        pub, "ProjectDependencies"
    ), "Expected `ProjectDependencies` to be defined in core.dbt.contracts.publication (renamed per review)."
    assert hasattr(
        pub, "ProjectDependency"
    ), "Expected `ProjectDependency` to be defined in core.dbt.contracts.publication (renamed per review)."

    assert not hasattr(
        pub, "Dependencies"
    ), "Did not expect legacy `Dependencies` to remain after rename to `ProjectDependencies`."
    assert not hasattr(
        pub, "DependentProjects"
    ), "Did not expect legacy `DependentProjects` to remain after rename to `ProjectDependency`."