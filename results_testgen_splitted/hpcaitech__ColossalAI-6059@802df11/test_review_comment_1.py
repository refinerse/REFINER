import torch

from colossalai.zero.low_level.bookkeeping.tensor_bucket import TensorBucket


def test_all_gather_fp8_uses_buffer_chunk_views():
    """
    Verify the structural change requested: fp8 all_gather should pass
    `list(buffer.chunk(world_size))` into all_gather_fp8 (views into one contiguous buffer),
    rather than allocating independent `empty_like` tensors.

    We make this observable by:
    - Patching dist.get_world_size to avoid initializing distributed
    - Patching all_gather_fp8 to (a) capture the output tensors, and (b) mutate only the first one
    Then we assert the captured tensors share the same underlying storage.
    """
    import colossalai.zero.low_level.bookkeeping.tensor_bucket as tb_mod

    old_get_world_size = tb_mod.dist.get_world_size
    old_all_gather_fp8 = tb_mod.all_gather_fp8

    tb_mod.dist.get_world_size = lambda group=None: 2

    observed = {}

    def fake_all_gather_fp8(output_tensors, input_tensor, group=None, fp8_format=None):
        assert isinstance(output_tensors, list) and len(output_tensors) == 2, (
            "Expected fp8 all_gather to pass a list of length == world_size into all_gather_fp8"
        )
        observed["out"] = output_tensors
        # Modify only the first output tensor; we do NOT assume anything about initial values
        # of other chunks since the buffer is allocated with torch.empty().
        output_tensors[0].fill_(123)

    tb_mod.all_gather_fp8 = fake_all_gather_fp8

    try:
        b = TensorBucket(size=16)
        b.add_to_bucket(torch.zeros(4, dtype=torch.float32))

        b.all_gather(group=None, fp8_communication=True)

        out0, out1 = observed["out"]

        # In the fixed implementation, outputs are chunk views of one contiguous buffer,
        # so they must share the same underlying storage.
        ptr0 = out0.untyped_storage().data_ptr()
        ptr1 = out1.untyped_storage().data_ptr()
        assert ptr0 == ptr1, (
            "Expected fp8 all_gather outputs to come from `buffer.chunk(world_size)` and thus "
            "share the same underlying storage. If this fails, outputs were likely allocated as "
            "independent tensors (e.g., via `empty_like`)."
        )

        # Also ensure they are distinct views (different data pointers) into that same storage.
        # This should hold for chunked views and helps ensure we truly got chunk semantics.
        assert out0.data_ptr() != out1.data_ptr(), (
            "Expected different chunks to be distinct views (different data pointers) even though "
            "they share the same underlying storage."
        )
    finally:
        tb_mod.dist.get_world_size = old_get_world_size
        tb_mod.all_gather_fp8 = old_all_gather_fp8