import re


def test_sdxl_img2img_uses_denoising_start_end_api_not_step_ints():
    """
    This test enforces the review-requested behavior change:
    - The pipeline should accept percentage-based denoising controls via `denoising_start` and `denoising_end`
      (both Optional[float]) instead of integer-step controls (`max_inference_steps`, `first_inference_step`).

    It is implemented via source inspection because importing diffusers fails in this environment.
    """
    path = "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_img2img.py"
    source = open(path, "r", encoding="utf-8").read()

    # Must expose denoising_start/end parameters in __call__ signature.
    assert "denoising_start" in source and "denoising_end" in source, (
        "Expected the pipeline to expose percentage-based controls `denoising_start` and `denoising_end` "
        "in StableDiffusionXLImg2ImgPipeline.__call__."
    )

    # Must NOT keep the old integer-step API parameters in __call__ signature.
    assert "max_inference_steps" not in source, (
        "Expected `max_inference_steps` (int-based early break API) to be removed in favor of `denoising_end`."
    )
    assert "first_inference_step" not in source, (
        "Expected `first_inference_step` (int-based start step API) to be removed in favor of `denoising_start`."
    )

    # Ensure denoising_end is applied by slicing timesteps (not by breaking the loop).
    assert "Apply denoising_end" in source or "denoising_end is not None" in source, (
        "Expected logic applying `denoising_end` (timestep slicing) to be present."
    )
    assert "Breaking inference loop" not in source, (
        "Did not expect inference loop early-break debug message; `denoising_end` should be applied by timestep slicing."
    )

    # Ensure get_timesteps supports denoising_start and rounds it to avoid misalignment.
    # (simple substring checks; no AST parsing).
    assert "def get_timesteps" in source and "denoising_start" in source, (
        "Expected get_timesteps() to accept `denoising_start` to support percentage-based start."
    )
    assert "int(round(denoising_start * num_inference_steps))" in source, (
        "Expected denoising_start to be converted using rounding: "
        "`t_start = int(round(denoising_start * num_inference_steps))` to avoid timestep misalignment."
    )

    # Ensure denoising_end uses rounding too (for consistent step counts).
    assert re.search(r"int\(round\(\s*denoising_end\s*\*\s*num_inference_steps\s*\)\)", source), (
        "Expected denoising_end to compute step counts using rounding, e.g. "
        "`num_inference_steps = int(round(denoising_end * num_inference_steps))`."
    )