import re

import pytest


FILE_PATH = "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl.py"


def test_sdxl_pipeline_uses_denoising_end_not_max_inference_steps_and_docs_updated():
    """
    The review requested replacing confusing "backwards pass" wording/parameter with `denoising_end`
    (fractional denoising) and updating the docstring accordingly.

    This test enforces:
      - public API argument is `denoising_end` (and not `max_inference_steps`)
      - docstring describes fractional termination and includes the refining-the-image-output link
      - implementation applies `denoising_end` by slicing timesteps (not by breaking the loop)
    """
    source = open(FILE_PATH, "r", encoding="utf-8").read()

    # 1) Signature: should contain denoising_end and not max_inference_steps
    assert "denoising_end: Optional[float] = None" in source, (
        "StableDiffusionXLPipeline.__call__ should accept `denoising_end: Optional[float] = None` "
        "instead of the old `max_inference_steps` parameter."
    )
    assert "max_inference_steps" not in source, (
        "The old `max_inference_steps` parameter should be removed entirely in favor of `denoising_end`."
    )

    # 2) Docstring: should describe fractional denoising and include the docs link from the example
    assert "determines the fraction (between 0.0 and 1.0) of the total denoising process" in source, (
        "Docstring for `denoising_end` should clearly explain that it is a fraction of the denoising process "
        "(to avoid confusion with a 'backwards pass')."
    )
    assert "refining-the-image-output" in source, (
        "Docstring for `denoising_end` should include a reference link to 'Refining the Image Output' "
        "as per the provided example."
    )

    # 3) Implementation: should slice timesteps based on denoising_end, not break mid-loop by step counter
    assert "timesteps = timesteps[: num_warmup_steps + self.scheduler.order * num_inference_steps]" in source, (
        "Implementation should apply `denoising_end` by adjusting `num_inference_steps` and slicing `timesteps`, "
        "not by breaking out of the inference loop based on a counter."
    )

    # Ensure old behavior (breaking the inference loop) is not present
    assert "Breaking inference loop" not in source and re.search(r"\bbreak\b", source) is None or (
        # allow other 'break' statements elsewhere, but not the old max_inference_steps guard
        "max_inference_steps is not None" not in source
    ), (
        "Old early-termination mechanism using `max_inference_steps` and a `break` in the denoising loop "
        "should not exist anymore."
    )