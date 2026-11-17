import re


def test_directory_build_props_removes_global_system_text_json_and_duplicate_warning_workaround():
    """
    The review comment suggests removing the global System.Text.Json package reference
    (and the related duplicate-package-warning workaround) from Directory.Build.props.
    This test enforces that structural cleanup.
    """
    path = "/workspace/dotnet/Directory.Build.props"
    source = open(path, "r", encoding="utf-8").read()

    assert "NoWarnDuplicatePackages" not in source, (
        "Directory.Build.props should not define NoWarnDuplicatePackages; "
        "the duplicate package warning workaround should be removed."
    )

    assert "Some properties require a different version of System.Json.Text" not in source, (
        "Directory.Build.props should not contain the comment justifying a duplicate package "
        "warning workaround; that workaround should be removed."
    )

    # Ensure we don't keep a global STJ package reference (review comment: remove S.T.J global reference).
    assert re.search(r'<PackageReference\s+Include="System\.Text\.Json"\s*/>', source) is None, (
        "Directory.Build.props should not contain a global "
        '<PackageReference Include="System.Text.Json" />; '
        "remove the global System.Text.Json reference."
    )