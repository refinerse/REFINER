import torch
import torch.distributed as dist

from colossalai.zero.low_level.bookkeeping.tensor_bucket import TensorBucket


def test_tensor_bucket_all_gather_uses_all_gather_into_tensor_for_non_fp8():
    """
    Structural expectation from review:
    - non-fp8 path should use dist.all_gather_into_tensor (single flat buffer),
      NOT dist.all_gather (list of per-rank buffers).

    We verify this by:
    - forcing world_size=2 via monkeypatching dist.get_world_size
    - temporarily replacing dist.all_gather and dist.all_gather_into_tensor with sentinels
      that record which one was called and validate the signature shape.
    """
    # Save originals to restore at end (avoid unittest.mock per requirements).
    orig_get_world_size = dist.get_world_size
    orig_all_gather = getattr(dist, "all_gather", None)
    orig_all_gather_into_tensor = getattr(dist, "all_gather_into_tensor", None)

    calls = {"all_gather": 0, "all_gather_into_tensor": 0}

    def fake_get_world_size(group=None):
        return 2

    def fake_all_gather(output_tensor_list, input_tensor, group=None, async_op=False):
        calls["all_gather"] += 1
        # Ensure it is the list-based API
        assert isinstance(
            output_tensor_list, (list, tuple)
        ), "dist.all_gather must be called with a list/tuple as the first argument"

    def fake_all_gather_into_tensor(output_tensor, input_tensor, group=None, async_op=False):
        calls["all_gather_into_tensor"] += 1
        # Ensure it is the into-tensor API with a single Tensor output
        assert isinstance(output_tensor, torch.Tensor), (
            "dist.all_gather_into_tensor must be called with a Tensor buffer "
            "as the first argument"
        )
        # Also validate expected size: world_size * input.numel()
        assert output_tensor.numel() == fake_get_world_size(group) * input_tensor.numel(), (
            "all_gather_into_tensor output buffer should have world_size * input.numel() elements"
        )

    try:
        dist.get_world_size = fake_get_world_size
        dist.all_gather = fake_all_gather
        dist.all_gather_into_tensor = fake_all_gather_into_tensor

        bucket = TensorBucket(size=1024)
        t = torch.arange(6, dtype=torch.float32)
        bucket.add_to_bucket(t)

        # Trigger non-fp8 branch; our fake dist ops do not actually communicate,
        # but we only care which API gets invoked.
        bucket.all_gather(group=None, fp8_communication=False)

        assert calls["all_gather_into_tensor"] == 1, (
            "TensorBucket.all_gather(fp8_communication=False) must call "
            "dist.all_gather_into_tensor for better performance (single flat buffer)."
        )
        assert calls["all_gather"] == 0, (
            "TensorBucket.all_gather(fp8_communication=False) should NOT call dist.all_gather "
            "(list-of-buffers API)."
        )
    finally:
        dist.get_world_size = orig_get_world_size
        if orig_all_gather is not None:
            dist.all_gather = orig_all_gather
        if orig_all_gather_into_tensor is not None:
            dist.all_gather_into_tensor = orig_all_gather_into_tensor