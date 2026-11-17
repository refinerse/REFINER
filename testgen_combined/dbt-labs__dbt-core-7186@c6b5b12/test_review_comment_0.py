import dataclasses

from core.dbt.contracts.graph import model_config


def test_delimiter_is_seed_only_config_field():
    """
    The review comment requests that `delimiter` be part of SeedConfig, not NodeConfig.
    This test enforces that:
      - NodeConfig does NOT declare a dataclass field named 'delimiter'
      - SeedConfig DOES declare a dataclass field named 'delimiter' with default ','
    """
    node_field_names = {f.name for f in dataclasses.fields(model_config.NodeConfig)}
    seed_field_names = {f.name for f in dataclasses.fields(model_config.SeedConfig)}

    assert (
        "delimiter" not in node_field_names
    ), "Expected 'delimiter' to NOT be a field on NodeConfig (it should be seed-only)."

    assert (
        "delimiter" in seed_field_names
    ), "Expected 'delimiter' to be a field on SeedConfig."

    seed_delimiter_default = model_config.SeedConfig().delimiter
    assert (
        seed_delimiter_default == ","
    ), "Expected SeedConfig.delimiter to default to ','"