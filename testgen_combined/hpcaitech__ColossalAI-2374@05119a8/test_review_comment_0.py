import re


def test_multi_tensor_copy_uses_global_fused_optim_not_multi_tensor_scale():
    source = open("/workspace/colossalai/amp/naive_amp/_fp16_optimizer.py", "r", encoding="utf-8").read()

    # Focus on the reviewed function to avoid false positives elsewhere.
    m = re.search(
        r"def _multi_tensor_copy_this_to_that\s*\(.*?\):(?P<body>.*?)(?:\n\nclass |\Z)",
        source,
        flags=re.DOTALL,
    )
    assert m is not None, "Expected to find function `_multi_tensor_copy_this_to_that` in the source file"
    body = m.group("body")

    assert (
        "global fused_optim" in body
    ), "Expected `_multi_tensor_copy_this_to_that` to declare `global fused_optim` before using fused_optim.multi_tensor_scale"

    assert (
        "global multi_tensor_scale" not in body
    ), "Did not expect stray `global multi_tensor_scale` (typo); should be `global fused_optim` instead"