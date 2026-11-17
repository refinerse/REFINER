def test_linux_xdg_dependency_append_is_multiline_dict_style():
    import re

    source = open("/workspace/spyder/dependencies.py", encoding="utf-8").read()

    # Look for the *requested* multiline style for the Linux-only xdg dependency.
    expected_multiline_pattern = re.compile(
        r"DEPENDENCIES_BASE\.append\(\s*\n"
        r"\s*\{\s*\n"
        r"\s*'modname':\s*\"xdg\",\s*\n"
        r"\s*'package_name':\s*\"pyxdg\",\s*\n"
        r"\s*'features':\s*_\([^)]*\),\s*\n"
        r"\s*'required_version':\s*PYXDG_REQVER\s*\n"
        r"\s*\}\s*\n"
        r"\s*\)\s*",
        re.MULTILINE,
    )
    assert expected_multiline_pattern.search(source), (
        "Expected the Linux 'xdg' dependency to be appended using the multiline "
        "DEPENDENCIES_BASE.append( ... ) style with the dict written one key per line."
    )

    # Ensure the old one-liner style is not used for xdg.
    old_oneliner_pattern = re.compile(
        r"DEPENDENCIES_BASE\.append\(\{[^\n]*'modname':\s*\"xdg\"[^\n]*\}\)",
        re.MULTILINE,
    )
    assert not old_oneliner_pattern.search(source), (
        "Found a one-line DEPENDENCIES_BASE.append({...}) for the Linux 'xdg' dependency; "
        "the review requested converting this to the multiline style."
    )