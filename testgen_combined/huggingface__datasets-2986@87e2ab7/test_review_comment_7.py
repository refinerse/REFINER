import re


def test_metric_module_dataclass_renamed_to_metricmodule():
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    # The review comment suggests renaming MetricModuleFactoryResult -> MetricModule.
    # The "after" code defines "@dataclass class MetricModule:" and removes the old name.
    assert re.search(r"@dataclass\s*\nclass\s+MetricModule\s*:", source), (
        "Expected src/datasets/load.py to define a dataclass named 'MetricModule' "
        "(renamed from the old MetricModuleFactoryResult)."
    )

    assert not re.search(r"@dataclass\s*\nclass\s+MetricModuleFactoryResult\s*:", source), (
        "Expected src/datasets/load.py to no longer define 'MetricModuleFactoryResult' after the rename to 'MetricModule'."
    )