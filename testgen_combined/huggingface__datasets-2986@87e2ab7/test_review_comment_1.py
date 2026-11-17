import re


def test_copy_function_is_renamed_and_docstring_updated():
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    # Functional expectation from the review comment:
    # the helper should be named "_copy_script_and_other_resources_in_importable_dir"
    assert (
        "def _copy_script_and_other_resources_in_importable_dir(" in source
    ), "Expected helper function to be named '_copy_script_and_other_resources_in_importable_dir' (renamed from the misspelled '_copy_script_and_other_resouces_in_importable_dir')."

    # Ensure the old misspelled name is gone (both definition and mentions)
    assert (
        "def _copy_script_and_other_resouces_in_importable_dir(" not in source
    ), "Did not expect old misspelled helper function definition '_copy_script_and_other_resouces_in_importable_dir' to remain."

    assert (
        "_copy_script_and_other_resouces_in_importable_dir" not in source
    ), "Did not expect any references to old misspelled helper name '_copy_script_and_other_resouces_in_importable_dir' to remain."

    # Also ensure the docstring mention for the downstream function name matches the new name
    # (this is observable behavior for users reading error/help messages and docs).
    assert (
        "_copy_script_and_other_resources_in_importable_dir" in source
    ), "Expected docstrings/comments to reference '_copy_script_and_other_resources_in_importable_dir' (not the old misspelling)."

    # Sanity: verify the renamed function signature uses 'subdirectory_name' (typo fix)
    # This helps ensure we matched the intended refactor, not just a superficial rename.
    m = re.search(
        r"def _copy_script_and_other_resources_in_importable_dir\((?P<args>[\s\S]*?)\)\s*:",
        source,
    )
    assert m, "Could not locate the full definition header for '_copy_script_and_other_resources_in_importable_dir'."
    header_args = m.group("args")
    assert (
        "subdirectory_name" in header_args
    ), "Expected parameter 'subdirectory_name' in renamed helper signature (typo fix from 'subdirrectory_name')."
    assert (
        "subdirrectory_name" not in header_args
    ), "Did not expect old misspelled parameter name 'subdirrectory_name' in helper signature."