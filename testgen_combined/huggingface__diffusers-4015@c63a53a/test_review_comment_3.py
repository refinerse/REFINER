import re

import pytest


FILEPATH = "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_img2img.py"


def _read_source():
    with open(FILEPATH, "r", encoding="utf-8") as f:
        return f.read()


def test_img2img_uses_denoising_end_api_not_first_inference_step_or_max_inference_steps():
    """
    Review request: "it would be nicer if we could use `denoising_end` here".
    We enforce that the pipeline switches to the public denoising_start/denoising_end API
    instead of the bespoke first_inference_step/max_inference_steps arguments.
    """
    source = _read_source()

    # Must expose denoising_end in __call__ signature (public API).
    assert "denoising_end" in source, (
        "Expected StableDiffusionXLImg2ImgPipeline.__call__ to expose `denoising_end` "
        "parameter (review request: use denoising_end), but it was not found in the source."
    )

    # Must not keep the old bespoke parameters around in __call__ signature.
    assert "first_inference_step" not in source, (
        "Expected the pipeline to stop using `first_inference_step` and instead rely on "
        "`denoising_start`/`denoising_end`, but `first_inference_step` is still present."
    )
    assert "max_inference_steps" not in source, (
        "Expected the pipeline to stop using `max_inference_steps` and instead rely on "
        "`denoising_end`, but `max_inference_steps` is still present."
    )

    # Also ensure the input check call no longer mentions first_inference_step.
    # This catches the original reviewed line that included first_inference_step in check_inputs.
    m = re.search(r"\bself\.check_inputs\s*\((?P<args>[\s\S]*?)\)\s*", source)
    assert m is not None, "Could not find a `self.check_inputs(...)` call in the pipeline source."
    args = m.group("args")
    assert "first_inference_step" not in args, (
        "Expected `self.check_inputs(...)` call to not include `first_inference_step` anymore. "
        "It should validate inputs without that bespoke argument when using denoising_end."
    )