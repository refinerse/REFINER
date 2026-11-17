import re


def test_call_once_and_share_no_longer_uses_two_queues_ack_sync():
    """
    Functional intent: the old implementation used a second Queue (queue_ack) as an
    imperfect synchronization mechanism; the updated implementation should remove
    that mechanism entirely (review comment suggests Barrier; final code uses
    torch.distributed + shared memory instead).

    This test is source-level because importing dgl fails in this environment
    (torch not installed).
    """
    source = open("/workspace/python/dgl/multiprocessing/pytorch.py", "r", encoding="utf-8").read()

    # Before version indicators (should be absent after fix)
    assert "queue_ack" not in source, (
        "call_once_and_share/spawn should not rely on a second Queue named 'queue_ack' for "
        "synchronization; the updated implementation should remove it."
    )

    assert "ProcessContext" not in source, (
        "Old implementation used ProcessContext(namedtuple) to carry queues/rank/nprocs; "
        "this should be removed in the updated implementation."
    )

    # After version indicators (should be present after fix)
    assert "torch.distributed.broadcast" in source, (
        "Updated implementation should broadcast shared memory identifier via "
        "torch.distributed.broadcast."
    )
    assert re.search(r"def\s+shared_tensor\s*\(", source), (
        "Updated implementation should provide shared_tensor() helper."
    )
    assert "create_shared_mem_array" in source and "get_shared_mem_array" in source, (
        "Updated implementation should use shared memory utilities "
        "create_shared_mem_array/get_shared_mem_array."
    )