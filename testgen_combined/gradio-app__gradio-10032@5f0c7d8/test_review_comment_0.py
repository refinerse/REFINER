import re


def test_image_webcam_constraints_documented_and_old_params_removed():
    source = open("/workspace/gradio/components/image.py", "r", encoding="utf-8").read()

    # Assert new API parameter exists (signature change)
    assert (
        "webcam_constraints" in source
    ), "Expected Image component to accept a `webcam_constraints` parameter (review request), but it was not found in gradio/components/image.py."

    # Assert old height/width params are removed (should fail on before code)
    assert (
        "webcam_height" not in source and "webcam_width" not in source
    ), "Expected `webcam_height`/`webcam_width` parameters to be removed in favor of `webcam_constraints`, but found old parameter names in gradio/components/image.py."

    # Assert documentation includes webcam_constraints description + demo reference
    assert (
        "webcam_constraints:" in source
    ), "Expected `webcam_constraints` to be documented in the Image.__init__ docstring (Parameters list), but 'webcam_constraints:' was not found."

    assert (
        "$demo/webcam_constraints" in source
    ), "Expected `webcam_constraints` docstring to reference '$demo/webcam_constraints' example, but it was not found."

    # Ensure it's typed as a dict in the signature (helps enforce "python dictionary" request)
    assert re.search(
        r"webcam_constraints\s*:\s*dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None",
        source,
    ), (
        "Expected `webcam_constraints` signature to be typed as `dict[str, Any] | None = None` "
        "to match the new API. This pattern was not found."
    )