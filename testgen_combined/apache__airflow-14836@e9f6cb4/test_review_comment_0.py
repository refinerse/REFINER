import re


def test_react_ui_precommit_hooks_use_node_language_and_file_filtering():
    """
    Verifies the React UI pre-commit hooks are configured as node hooks and
    restricted to UI TS/TSX files (not a system hook calling a script).
    """
    source = open("/workspace/.pre-commit-config.yaml", encoding="utf-8").read()

    # The "before" version used a single system hook "ui-lint-test" calling a script.
    assert (
        "id: ui-lint-test" not in source
    ), "React UI hook should not be a single 'ui-lint-test' system hook; it should be split into node-based hooks."

    # The "after" version should contain separate lint and test hooks.
    assert (
        "id: ui-lint" in source and "id: ui-test" in source
    ), "Expected separate React UI hooks 'ui-lint' and 'ui-test' to be present in .pre-commit-config.yaml."

    # Each hook should use pre-commit's node language and define a files regex scoped to airflow/ui TS/TSX files.
    for hook_id in ("ui-lint", "ui-test"):
        # Find the hook block; keep it simple and robust by scanning until the next '- id:' at same indentation.
        m = re.search(
            rf"(?ms)^[ \t]*- id:\s*{re.escape(hook_id)}\s*$"
            rf"(.*?)"
            rf"(?=^[ \t]*- id:|\Z)",
            source,
        )
        assert m, f"Could not locate hook block for '{hook_id}' in .pre-commit-config.yaml."
        block = m.group(1)

        assert re.search(
            r"(?m)^[ \t]*language:\s*node\s*$", block
        ), f"Hook '{hook_id}' should use 'language: node' so pre-commit manages the Node environment."

        assert re.search(
            r"(?m)^[ \t]*files:\s*\^airflow/ui/.*\\\.\(ts\|tsx\)\$\s*$", block
        ), (
            f"Hook '{hook_id}' must define a 'files:' regex targeting only airflow/ui TS/TSX files "
            "so pre-commit runs it only for changed UI files."
        )