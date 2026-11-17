import re

import pytest


PIPELINE_FILE = "/workspace/src/diffusers/pipelines/stable_diffusion/pipeline_stable_diffusion.py"


def test_stable_diffusion_pipeline_always_casts_image_to_float32_before_numpy():
    """
    Regression test for image->numpy conversion in StableDiffusionPipeline.__call__:

    The reviewed change removes dtype-dependent branching and always casts to float32
    before calling .numpy(), ensuring compatibility with bfloat16 tensors on CPU.
    """
    source = open(PIPELINE_FILE, "r", encoding="utf-8").read()

    # Must include the new one-liner conversion (allow whitespace/newlines variations).
    pattern = r"image\s*=\s*image\.cpu\(\)\.permute\(\s*0\s*,\s*2\s*,\s*3\s*,\s*1\s*\)\.float\(\)\.numpy\(\)"
    assert re.search(pattern, source), (
        "Expected StableDiffusionPipeline to always cast image to float32 before converting to numpy via:\n"
        "    image = image.cpu().permute(0, 2, 3, 1).float().numpy()\n"
        "This ensures bfloat16 compatibility without dtype-dependent branching."
    )

    # Must not retain the old dtype-based bfloat16 special-casing branch.
    assert "if image.dtype == torch.bfloat16" not in source, (
        "Did not expect dtype-conditional conversion for bfloat16 (e.g., `if image.dtype == torch.bfloat16:`). "
        "The conversion should be unconditional `.float().numpy()`."
    )