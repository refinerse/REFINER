import re

import pytest


FILE_PATH = "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl.py"


def test_sdxl_pipeline_uses_denoising_end_fraction_and_removes_max_inference_steps():
    """
    This test enforces the reviewed behavior change:
      - Replace `max_inference_steps` (break-by-index) with `denoising_end` (fraction of total denoising).
      - Ensure the denoising loop is shortened by slicing `timesteps` based on `denoising_end`.
    """
    source = open(FILE_PATH, "r", encoding="utf-8").read()

    # 1) Public API: __call__ signature should expose denoising_end and not max_inference_steps
    assert "denoising_end: Optional[float] = None" in source, (
        "Expected SDXL pipeline __call__ signature to include `denoising_end: Optional[float] = None`."
    )
    assert "max_inference_steps: Optional[int] = None" not in source, (
        "Expected `max_inference_steps` to be removed from SDXL pipeline __call__ signature (replaced by denoising_end)."
    )

    # 2) Behavior: should apply denoising_end as fraction of num_inference_steps and slice timesteps accordingly.
    assert "if denoising_end is not None:" in source, (
        "Expected `denoising_end` to be applied inside __call__ (missing `if denoising_end is not None:` block)."
    )

    # Must compute a new num_inference_steps from the fraction with rounding.
    assert re.search(r"num_inference_steps\s*=\s*int\(\s*round\(\s*denoising_end\s*\*\s*num_inference_steps\s*\)\s*\)", source), (
        "Expected `num_inference_steps` to be recomputed as `int(round(denoising_end * num_inference_steps))` "
        "to handle rounding behavior up-front."
    )

    # Must slice timesteps to stop early (not break by loop index).
    assert re.search(r"timesteps\s*=\s*timesteps\[:\s*num_warmup_steps\s*\+\s*self\.scheduler\.order\s*\*\s*num_inference_steps\s*\]", source), (
        "Expected timesteps to be truncated based on `denoising_end` using "
        "`timesteps = timesteps[: num_warmup_steps + self.scheduler.order * num_inference_steps]`."
    )

    # 3) Ensure the old behavior (break loop at max_inference_steps) is not present.
    assert "Breaking inference loop" not in source and "i >= max_inference_steps" not in source, (
        "Did not expect the old `max_inference_steps` break-based early termination logic to remain in the file."
    )