import pytest

from rasa.nlu.components import validate_required_components_from_data
from rasa.nlu.training_data import TrainingData


class _FakeComponent:
    def __init__(self, name: str, config=None):
        self._name = name
        self.component_config = config or {}

    @property
    def name(self) -> str:
        return self._name


def test_lookup_table_warning_message_mentions_make_use_not_featurize():
    """If lookup tables exist and neither DIET nor CRF is in the pipeline,
    the warning should not claim DIET 'featurizes' lookup tables (it doesn't).
    It should say 'make use of lookup tables' instead.
    """
    data = TrainingData()
    data.lookup_tables = [{"name": "cities", "elements": ["Berlin", "Paris"]}]

    pipeline = [_FakeComponent("RegexFeaturizer")]

    with pytest.warns(UserWarning) as record:
        validate_required_components_from_data(pipeline, data)

    messages = "\n".join(str(w.message) for w in record)
    assert (
        "To make use of lookup tables" in messages
    ), f"Expected warning to say DIET/CRF 'make use of lookup tables', but got:\n{messages}"
    assert (
        "To featurize lookup tables, add a 'DIETClassifier'" not in messages
    ), (
        "Warning should not suggest that DIETClassifier featurizes lookup tables. "
        f"Got:\n{messages}"
    )