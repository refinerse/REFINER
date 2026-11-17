import datetime

from taipy.config.common.frequency import Frequency
from taipy.config.config import Config
from taipy.core.scenario._scenario_manager import _ScenarioManager


def test_sort_scenarios_uses_id_tiebreaker_for_equal_values():
    """
    Review request: sorting should be predictable when two scenarios share the same value
    (e.g., same tags), by using scenario.id as a second criterion.
    This should fail on the "before" code (no id tiebreak -> order depends on insertion),
    and pass on the "after" code (id tiebreak -> deterministic, matches Python tuple sort).
    """
    cfg = Config.configure_scenario(id="tie_cfg", frequency=Frequency.DAILY)

    now = datetime.datetime.now()
    # Ensure different cycles so both can be primary simultaneously.
    s_late = _ScenarioManager._create(cfg, now + datetime.timedelta(days=2), "same_tags")
    s_early = _ScenarioManager._create(cfg, now + datetime.timedelta(days=4), "same_tags")

    _ScenarioManager._set_primary(s_late)
    _ScenarioManager._set_primary(s_early)

    # Same sort key value -> requires stable/deterministic tie-break.
    s_late.tags = ["banana", "kiwi"]
    s_early.tags = ["banana", "kiwi"]

    primary = _ScenarioManager._get_primary_scenarios()
    assert s_late in primary and s_early in primary, "Precondition failed: both scenarios must be primary."

    result = _ScenarioManager._sort_scenarios(primary, descending=False, sort_key="tags")

    # Expected behavior after fix: sort by (tags, id)
    expected = sorted(primary, key=lambda s: (s.tags, s.id))
    assert result == expected, (
        "Sorting by 'tags' must be deterministic when scenarios share the same tags: "
        "tie-break must use scenario.id (i.e., sort by (tags, id))."
    )