import re


def test_deprecation_issue_installation_type_is_conditional_on_is_haos() -> None:
    """Ensure installation_type placeholder reflects is_haos (OS vs Supervised).

    Regression for review: when the issue is created due to deprecated_architecture
    (even on HAOS), installation_type must not always be "Supervised".
    """
    source = open("/workspace/homeassistant/components/hassio/__init__.py").read()

    # The fixed code must include conditional installation_type mapping.
    assert (
        '"installation_type": "OS" if is_haos else "Supervised"' in source
    ), (
        "Expected hassio deprecated issue creation to set translation_placeholders['installation_type'] "
        'to conditional value: "OS" if is_haos else "Supervised". '
        "This ensures HAOS installations that trigger the deprecation warning due to architecture "
        "do not incorrectly report 'Supervised'."
    )

    # Guardrail: old buggy pattern should not remain (unconditional 'Supervised').
    assert not re.search(
        r'"installation_type"\s*:\s*"Supervised"\s*,\s*\n\s*"arch"\s*:\s*arch',
        source,
    ), (
        "Found unconditional translation_placeholders['installation_type'] == 'Supervised' "
        "in the deprecated issue creation block; this would mislabel HAOS installs."
    )