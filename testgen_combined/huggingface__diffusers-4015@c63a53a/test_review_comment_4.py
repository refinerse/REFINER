import re


FILE_PATH = "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_img2img.py"


def test_denoising_start_controls_add_noise_and_replaces_first_inference_step():
    source = open(FILE_PATH, "r", encoding="utf-8").read()

    # The review addressed: replace implicit "first_inference_step" logic with an explicitly-defined
    # "denoising_start" parameter and ensure add_noise depends on denoising_start (not first_inference_step).
    assert "denoising_start" in source, (
        "Expected the pipeline to define/use the explicit `denoising_start` parameter to control where denoising "
        "starts (and whether to add initial noise)."
    )

    assert "first_inference_step" not in source, (
        "The old `first_inference_step` mechanism should be removed in favor of `denoising_start`/`denoising_end`. "
        "Found `first_inference_step` still present in the pipeline source."
    )

    # Check for the new add_noise logic (must depend on denoising_start).
    # Accept minor formatting variations.
    pattern = r"add_noise\s*=\s*True\s*if\s*denoising_start\s+is\s+None\s+else\s+False"
    assert re.search(pattern, source), (
        "Expected `add_noise` to be explicitly controlled by `denoising_start` (add noise only when "
        "`denoising_start is None`). Pattern not found."
    )