import mypy.test.testmodulefinder as tmf


def test_modulefinder_tests_do_not_define_expand_site_packages_helper() -> None:
    """
    Structural regression test:

    The old test module defined its own `expand_site_packages()` helper to emulate
    .pth parsing. After the change, the site-packages tests list package_path
    entries explicitly and no longer need any .pth expansion helpers.

    Enforce that `mypy.test.testmodulefinder` does not define these helpers.
    """
    assert not hasattr(
        tmf, "expand_site_packages"
    ), "testmodulefinder should not define an expand_site_packages() helper; package paths should be listed explicitly."
    assert not hasattr(
        tmf, "_parse_pth_file"
    ), "testmodulefinder should not include .pth parsing helpers (_parse_pth_file) now that .pth files are not used."
    assert not hasattr(
        tmf, "_make_abspath"
    ), "testmodulefinder should not include .pth parsing helpers (_make_abspath) now that .pth files are not used."


def test_modulefinder_site_packages_suite_lists_package_paths_explicitly() -> None:
    """
    Verify the new explicit package_path listing is present in the source,
    and that the old `.pth`-based expansion call is gone.

    Note: The file may still mention ".pth" in comments in test cases (e.g.
    "Packages found by following .pth files"). That's OK; what we care about
    is that no code expands/parses .pth files anymore.
    """
    source = open("/workspace/mypy/test/testmodulefinder.py", "r", encoding="utf8").read()

    assert "package_paths = (" in source, (
        "ModuleFinderSitePackagesSuite.setUp() should define an explicit 'package_paths' tuple "
        "instead of expanding .pth files."
    )
    assert "package_path=tuple(package_paths)" in source, (
        "ModuleFinderSitePackagesSuite.setUp() should pass the explicit package_paths tuple into SearchPaths."
    )
    assert "expand_site_packages(" not in source, (
        "ModuleFinderSitePackagesSuite.setUp() should not call expand_site_packages(); "
        "site-packages package_path entries should be listed explicitly."
    )
    # Additional guard to ensure the old helper implementation isn't reintroduced.
    assert "def _parse_pth_file" not in source and "def _make_abspath" not in source, (
        "testmodulefinder should not implement .pth parsing helpers anymore; it should use explicit package paths."
    )