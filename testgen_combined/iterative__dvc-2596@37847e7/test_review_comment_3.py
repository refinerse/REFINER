import re


def test_replace_hyphen_is_nested_inside__dvc_function():
    source = open("/workspace/scripts/completion/dvc.bash", encoding="utf-8").read()

    # Style requirement from review: helper function should be scoped within `_dvc`
    # to avoid global namespace collisions.
    assert "replace_hyphen ()" in source, "Expected `replace_hyphen ()` to exist in dvc.bash."

    # Ensure there is no *global* definition of replace_hyphen (i.e., at top-level).
    # We consider it global if it appears before the `_dvc () {` function definition.
    dvc_match = re.search(r"(?m)^_dvc\s*\(\)\s*\{", source)
    assert dvc_match, "Expected `_dvc () {` function definition to exist in dvc.bash."

    first_replace_idx = source.find("replace_hyphen ()")
    assert (
        first_replace_idx > dvc_match.start()
    ), (
        "`replace_hyphen ()` must be defined inside `_dvc` (nested function) to avoid "
        "polluting the global bash namespace, but a definition was found before `_dvc () {`."
    )