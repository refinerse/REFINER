import importlib


def test_yaml_helper_uses_pyyaml_not_oyaml():
    """
    Functional regression check without relying on pytest runtime.

    The behavioral issue discussed in the review comment stems from switching
    yaml_helper to use oyaml. We assert at runtime that yaml_helper's `yaml`
    reference is backed by the `yaml` (PyYAML) package, not `oyaml`.
    """
    yaml_helper = importlib.import_module("core.dbt.clients.yaml_helper")
    importlib.reload(yaml_helper)  # ensure we observe current module state

    yaml_module_name = getattr(yaml_helper.yaml, "__name__", None)
    assert yaml_module_name == "yaml", (
        "core.dbt.clients.yaml_helper must use PyYAML (`import yaml`), not oyaml "
        "(`import oyaml as yaml`), because oyaml can change dumping/sorting behavior. "
        f"Observed yaml_helper.yaml.__name__={yaml_module_name!r}."
    )