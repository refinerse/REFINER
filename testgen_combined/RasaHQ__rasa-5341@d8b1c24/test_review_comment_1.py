import pytest

from rasa.nlu.components import validate_required_components_from_data


class DummyTrainingData:
    """Minimal stand-in for rasa.nlu.training_data.training_data.TrainingData.

    validate_required_components_from_data only relies on these attributes.
    """

    def __init__(
        self,
        *,
        response_examples=None,
        entity_examples=None,
        regex_features=None,
        lookup_tables=None,
        entity_synonyms=None,
    ):
        self.response_examples = response_examples or []
        self.entity_examples = entity_examples or []
        self.regex_features = regex_features or []
        self.lookup_tables = lookup_tables or []
        self.entity_synonyms = entity_synonyms or []


class DummyComponent:
    """Minimal stand-in for rasa.nlu.components.Component instances in a pipeline."""

    def __init__(self, name, features):
        self._name = name
        self.component_config = {"features": features}

    @property
    def name(self):
        return self._name


def test_validate_required_components_from_data_warns_if_last_crf_lacks_pattern_due_to_overwrite_bug():
    """Regression test capturing the behavior change in the review comment.

    When multiple CRFEntityExtractors exist, `has_pattern_feature` was set to True if
    any CRF had 'pattern'. The reviewed change makes `has_pattern_feature` get assigned
    each iteration (overwriting previous values), so if the *last* CRF lacks 'pattern',
    a warning is emitted.

    This test asserts the new (post-review) behavior: a warning is raised in that case.
    """
    data = DummyTrainingData(lookup_tables=[{"name": "cities", "elements": ["Berlin"]}])

    # Include RegexFeaturizer to avoid unrelated warnings about lookup tables.
    pipeline = [
        DummyComponent("RegexFeaturizer", features=[]),
        # First CRF includes pattern.
        DummyComponent("CRFEntityExtractor", features=[["pattern"], [], []]),
        # Last CRF does not include pattern -> should trigger warning after change.
        DummyComponent("CRFEntityExtractor", features=[["low"], [], []]),
    ]

    with pytest.warns(UserWarning) as recorded:
        validate_required_components_from_data(pipeline, data)

    assert any(
        "does not include the 'pattern' feature" in str(w.message) for w in recorded
    ), (
        "Expected a warning about CRFEntityExtractor missing the 'pattern' feature when "
        "the last CRFEntityExtractor in the pipeline lacks 'pattern' (post-review behavior)."
    )