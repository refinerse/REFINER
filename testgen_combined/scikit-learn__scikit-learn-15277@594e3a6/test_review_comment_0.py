import re


def test_azure_pipeline_linting_uses_combined_linting_script():
    source = open("/workspace/azure-pipelines.yml", encoding="utf-8").read()

    # The style change requested in the review was to combine two lint commands
    # into a single script "linting.sh" and have Azure call that script.
    assert "./build_tools/circle/linting.sh" in source, (
        "Expected Azure pipeline linting job to call the combined lint script "
        "'./build_tools/circle/linting.sh' (per review)."
    )

    # Ensure the old separate lint steps are no longer referenced in Azure.
    assert "./build_tools/circle/flake8_diff.sh" not in source, (
        "Found legacy lint command './build_tools/circle/flake8_diff.sh' in "
        "azure-pipelines.yml. Linting should be consolidated into linting.sh."
    )
    assert "./build_tools/circle/check_deprecated_properties.sh" not in source, (
        "Found legacy lint command './build_tools/circle/check_deprecated_properties.sh' in "
        "azure-pipelines.yml. Linting should be consolidated into linting.sh."
    )

    # Optional sanity check: the linting job should only run one script (not both).
    # This keeps the test focused on the consolidation intent.
    linting_job_block = re.search(
        r"(?ms)^\s*-\s*job:\s*linting\b.*?(?=^\s*-\s*(job:|template:)\b|\Z)",
        source,
    )
    assert linting_job_block, "Could not locate the 'linting' job block in azure-pipelines.yml."
    assert linting_job_block.group(0).count("./build_tools/circle/") == 1, (
        "Expected linting job to run exactly one build_tools/circle script (linting.sh) "
        "after consolidation."
    )