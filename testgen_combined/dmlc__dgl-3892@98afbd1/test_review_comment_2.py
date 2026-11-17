import re


def test_uva_sampling_not_reverted_in_dataloader_config():
    source = open("/workspace/examples/pytorch/graphsage/node_classification.py").read()

    # This review comment indicates a revert: the example should NOT switch to
    # multi-worker CPU sampling without UVA (i.e., "num_workers=12, use_uva=False, persistent_workers=True").
    #
    # BEFORE (should fail this test): those reverted settings are present.
    # AFTER  (should pass this test): those reverted settings are absent and
    #                                 uses num_workers=0 with use_uva conditional.
    forbidden_pattern = re.compile(
        r"num_workers\s*=\s*12\s*,\s*use_uva\s*=\s*False\s*,\s*persistent_workers\s*=\s*True"
    )

    assert not forbidden_pattern.search(source), (
        "Found reverted DataLoader settings (num_workers=12, use_uva=False, "
        "persistent_workers=True). The example should not disable UVA sampling "
        "and switch to multi-worker sampling here; it should keep the reverted behavior."
    )

    # Also ensure the expected post-revert behavior is present to make the test
    # specifically target the revert (and not just absence of a string).
    assert "num_workers=0" in source and "use_uva=not args.pure_gpu" in source, (
        "Expected the example to configure dataloaders with num_workers=0 and "
        "use_uva conditional on '--pure-gpu' (use_uva=not args.pure_gpu)."
    )