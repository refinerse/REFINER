import altair.utils._importers as importers


def test_import_toolz_function_removed_from_importers_module():
    """
    Regression test for removal of deprecated/unused helper.

    The review comment/PR removed altair.utils._importers.import_toolz_function.
    This test enforces that the symbol is not present on the module.
    """
    assert not hasattr(
        importers, "import_toolz_function"
    ), "import_toolz_function() should have been removed from altair.utils._importers"