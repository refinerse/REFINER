import inspect

from taipy.core.scenario._scenario_manager import _ScenarioManager


def test_sort_scenarios_supports_config_id_and_is_a_dedicated_method():
    # The review introduced a dedicated _sort_scenarios() method and added "config_id" as a supported sort_key.
    assert hasattr(
        _ScenarioManager, "_sort_scenarios"
    ), "Expected _ScenarioManager to define a dedicated _sort_scenarios() method for scenario ordering."

    sig = inspect.signature(_ScenarioManager._sort_scenarios)
    assert (
        "sort_key" in sig.parameters
    ), "Expected _sort_scenarios() to expose a 'sort_key' parameter (to support configurable sorting)."

    # Ensure the new business-meaningful key requested in review ("config_id") is supported by the API surface.
    sort_key_ann = sig.parameters["sort_key"].annotation
    assert (
        sort_key_ann is not inspect._empty and "config_id" in str(sort_key_ann)
    ), (
        "Expected _ScenarioManager._sort_scenarios(sort_key=...) to support 'config_id' "
        "in its Literal annotation (requested in review). "
        f"Got annotation: {sort_key_ann!r}"
    )

    # Functional check: sorting by config_id should work (and should be deterministic via id tiebreaker).
    class _DummyScenario:
        def __init__(self, scenario_id, name, config_id, creation_date=None, tags=None):
            self.id = scenario_id
            self.name = name
            self.config_id = config_id
            self.creation_date = creation_date
            self.tags = tags or set()

    scenarios = [
        _DummyScenario("b", "N2", "B"),
        _DummyScenario("a", "N1", "A"),
        _DummyScenario("c", "N3", "A"),
    ]
    out = _ScenarioManager._sort_scenarios(scenarios, sort_key="config_id")
    assert [s.id for s in out] == ["a", "c", "b"], (
        "Expected sorting by config_id to order scenarios by config_id, "
        "with a stable deterministic tiebreaker on id."
    )