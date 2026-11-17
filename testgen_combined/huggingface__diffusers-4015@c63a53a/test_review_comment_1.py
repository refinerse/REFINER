import re

import pytest


SOURCE_PATH = "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_img2img.py"


def _get_source():
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_img2img_get_timesteps_uses_denoising_start_and_not_first_inference_step():
    """
    Functional intent of review:
    - The pipeline should not try to "overwrite strength" when starting from a particular denoising fraction;
      instead it should pass denoising_start into get_timesteps, where strength is intentionally ignored.
    - API should use denoising_start/denoising_end (mixture-of-denoisers style), not first_inference_step.
    """
    source = _get_source()

    # After fix: get_timesteps signature includes denoising_start and __call__ passes denoising_start=...
    assert "def get_timesteps(self, num_inference_steps, strength, device, denoising_start=None):" in source, (
        "Expected StableDiffusionXLImg2ImgPipeline.get_timesteps to accept `denoising_start` and have signature "
        "(num_inference_steps, strength, device, denoising_start=None). This ensures starting at a particular "
        "denoising fraction is handled inside get_timesteps and strength is not incorrectly 'overwritten'."
    )

    assert re.search(
        r"timesteps,\s*num_inference_steps\s*=\s*self\.get_timesteps\(\s*"
        r"num_inference_steps\s*,\s*strength\s*,\s*device\s*,\s*denoising_start\s*=\s*denoising_start\s*\)",
        source,
        flags=re.MULTILINE,
    ), (
        "Expected __call__ to invoke get_timesteps with `denoising_start=denoising_start` (and not with "
        "`first_inference_step`). This matches the intended behavior where strength is ignored when starting "
        "midway through the denoising schedule."
    )

    # Before code had first_inference_step plumbing. After fix, that should be gone from __call__ signature.
    assert "first_inference_step" not in source, (
        "Did not expect `first_inference_step` to be present in the pipeline after the fix. The corrected API uses "
        "`denoising_start`/`denoising_end` and routes `denoising_start` into get_timesteps."
    )