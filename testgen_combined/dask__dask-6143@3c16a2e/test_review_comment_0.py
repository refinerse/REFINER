import re


def test_debugging_docs_logging_example_is_yaml_and_uses_config_glob_path():
    source = open("/workspace/docs/source/debugging.rst", encoding="utf-8").read()

    # The review requested switching the complex logging example from Python code
    # (mutating dask.config at runtime) to a YAML example suitable for dask config files.

    # 1) The 'after' version references standard config location with glob.
    assert (
        "``~/.config/dask/*.yaml`` files" in source
    ), "Expected docs to reference standard dask config location via the ~/.config/dask/*.yaml glob."

    # 2) The complex example should be YAML (not Python code that assigns into dask.config).
    # We do NOT assert there are no python code blocks in the whole file (there are many
    # unrelated Python examples elsewhere in the debugging docs).
    assert (
        "dask.config.config['logging']" not in source
    ), "Docs should not instruct setting logging by mutating dask.config.config['logging'] in code."

    # 3) Ensure the YAML logging config example exists and includes the required 'version: 1'
    # nested under a top-level 'logging:' key.
    assert re.search(
        r"(?ms)^\.\. code-block:: yaml\s*\n\nlogging:\n  version: 1\n",
        source,
    ), "Expected a YAML code block showing a top-level 'logging:' mapping with nested 'version: 1'."