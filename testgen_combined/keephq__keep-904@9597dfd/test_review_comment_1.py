import pytest

import keep.api.models.db.preset as preset_mod


def test_preset_is_private_defaults_to_false():
    """
    The review discussion questioned why `is_private` exists alongside `created_by`.
    The addressed change makes `is_private` explicitly default to False (instead of being nullable/None),
    which documents the intended behavior via the model default.
    """
    Preset = preset_mod.Preset
    PresetDto = preset_mod.PresetDto

    preset_instance = Preset(tenant_id="t1", name="n1", options=[])
    assert (
        preset_instance.is_private is False
    ), "Preset.is_private should default to False (not None) to clearly document non-private by default."

    dto_instance = PresetDto(id=preset_instance.id, name="n1", options=[])
    assert (
        dto_instance.is_private is False
    ), "PresetDto.is_private should default to False (not None) to match the model and document default behavior."