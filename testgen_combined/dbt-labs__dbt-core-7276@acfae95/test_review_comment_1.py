import core.dbt.contracts.publication as publication


def test_project_dependency_rename_applied():
    """
    Style regression test for naming change requested in review:
    `DependentProjects` -> `ProjectDependency`.
    """
    assert hasattr(
        publication, "ProjectDependency"
    ), "Expected class `ProjectDependency` to exist in core.dbt.contracts.publication (rename from `DependentProjects`)."

    assert not hasattr(
        publication, "DependentProjects"
    ), "Did not expect legacy class name `DependentProjects` to remain after renaming to `ProjectDependency`."