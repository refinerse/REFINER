import mypy.moduleinfo as moduleinfo


def test_third_party_modules_uses_importable_package_name_for_dateutil() -> None:
    """
    The third_party_modules collection is meant to contain importable module/package
    names (not PyPI distribution names). The PyPI project is "python-dateutil", but
    the importable package is "dateutil".
    """
    tpm = moduleinfo.third_party_modules

    assert "dateutil" in tpm, (
        "third_party_modules must include the importable package name 'dateutil' "
        "(PyPI distribution is 'python-dateutil')."
    )
    assert "python-dateutil" not in tpm, (
        "third_party_modules must not include the PyPI distribution name "
        "'python-dateutil'; this file should list importable package/module names."
    )