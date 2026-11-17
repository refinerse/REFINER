import re


def test_safety_checker_always_casts_to_float32_before_numpy():
    source_path = "/workspace/src/diffusers/pipelines/stable_diffusion/safety_checker.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # The intended behavior after the review: always cast to float32 before numpy(),
    # not conditionally based on dtype (e.g. bfloat16).
    #
    # We check for the presence of the chained call ".cpu().float().numpy()" on both
    # cosine distance tensors, which should exist in the "after" code.
    assert (
        ".cpu().float().numpy()" in source
    ), "Expected safety_checker forward() to always cast to float32 before numpy() via '.cpu().float().numpy()'"

    # Ensure the old conditional casting logic is gone (it would exist in the 'before' code).
    assert (
        "if image_embeds.dtype == torch.bfloat16" not in source
    ), "Did not expect dtype-conditional casting for bfloat16; forward() should always cast to float32 before numpy()"

    # Additionally ensure both tensors use the chained cast (not just one).
    # Use regex to be tolerant to whitespace/newlines.
    special_ok = re.search(
        r"special_cos_dist\s*=\s*cosine_distance\([^\)]*\)\.cpu\(\)\.float\(\)\.numpy\(\)",
        source,
    )
    concept_ok = re.search(
        r"cos_dist\s*=\s*cosine_distance\([^\)]*\)\.cpu\(\)\.float\(\)\.numpy\(\)",
        source,
    )

    assert special_ok is not None and concept_ok is not None, (
        "Expected both special_cos_dist and cos_dist to be computed with "
        "'.cpu().float().numpy()' to ensure numpy compatibility (e.g. bfloat16)."
    )