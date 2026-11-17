import re


def test_sdxl_img2img_uses_denoising_start_parameter_in_call_signature():
    source = open(
        "/workspace/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_img2img.py",
        "r",
        encoding="utf-8",
    ).read()

    # Core expectation from the review: __call__ exposes denoising_start as Optional[float] defaulting to None.
    # Before version: does NOT have this (it has max_inference_steps/first_inference_step instead) -> FAIL.
    # After version: has it -> PASS.
    assert (
        "denoising_start: Optional[float] = None" in source
    ), "Expected `denoising_start: Optional[float] = None` to be present in the pipeline's __call__ signature."

    # Additionally, ensure legacy parameter `first_inference_step` is not in __call__ signature anymore.
    # Use a robust, non-regex-crashy way to grab the __call__ signature block.
    start = source.find("def __call__(")
    assert start != -1, "Could not find `def __call__(` in the pipeline source."

    end = source.find("):", start)
    assert end != -1, "Could not find the end of the `__call__` signature (missing '):' after `def __call__(`)."

    call_sig = source[start : end + 2]
    assert (
        "first_inference_step" not in call_sig
    ), "Did not expect `first_inference_step` to still be present in `__call__` signature after introducing `denoising_start`."