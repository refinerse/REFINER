import re


def test_release_script_uses_is_alpha_property_and_version_param_instead_of_prerelease_tuple_logic():
    source = open("/workspace/scripts/release.py", encoding="utf-8").read()

    # The style review requested to hide the prerelease tuple validation logic behind
    # a property like `is_alpha_version` / `version.is_alpha` rather than inlining:
    # (
    #   len(version_object.prerelease) == 1
    #   and validate_alpha_version_part(version_object.prerelease[0])
    # )
    #
    # In the "before" code, this exact tuple logic is present. In the "after" code,
    # prerelease handling uses Version properties (e.g. `version.is_alpha` / `version.pre`)
    # and the validation function is gone.
    forbidden_inline_logic = (
        "len(version_object.prerelease) == 1"
        in source
        and "validate_alpha_version_part(version_object.prerelease[0])" in source
    )
    assert (
        not forbidden_inline_logic
    ), (
        "Expected scripts/release.py to avoid inlining alpha prerelease tuple logic "
        "(len(version_object.prerelease) == 1 and validate_alpha_version_part(...)) "
        "and instead rely on a Version-level property (e.g. version.is_alpha / "
        "is_alpha_version) with a `version: Version` parameter."
    )

    # Positive check: the refactor should use the Version property in workflow logic.
    assert (
        "version.is_alpha" in source
    ), "Expected scripts/release.py to use a Version-level alpha property (e.g. `version.is_alpha`)."

    # Extra guard: the old validation helper should not exist anymore after refactor.
    assert (
        "def validate_version(" not in source
    ), "Expected `validate_version` helper to be removed after moving alpha logic behind Version properties."