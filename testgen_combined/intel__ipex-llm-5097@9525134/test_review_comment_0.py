import re

AUTOFORMER_PATH = "/workspace/python/chronos/src/bigdl/chronos/model/autoformer/Autoformer.py"


def test_lr_scheduler_can_be_configured_or_disabled_via_config():
    """
    Review requirement:
    - allow users to set scheduler / milestones
    - allow users to disable scheduler
    Since torch is unavailable in this environment, verify via source inspection.
    """
    source = open(AUTOFORMER_PATH, "r", encoding="utf-8").read()

    # 1) Must not hardcode milestones=[3,4,5,6,7,8,9,10]
    assert "milestones=[3,4,5,6,7,8,9,10]" not in source, (
        "AutoFormer.configure_optimizers() should not hardcode MultiStepLR milestones; "
        "milestones must be configurable by users."
    )

    # 2) Must read milestones from config and allow disabling via None
    assert "lr_scheduler_milestones" in source, (
        "AutoFormer should expose a 'lr_scheduler_milestones' config option to let users "
        "set milestones or disable the scheduler."
    )

    # 3) Must conditionally create scheduler only when milestones is not None
    assert re.search(r"if\s+self\.lr_scheduler_milestones\s+is\s+not\s+None\s*:", source), (
        "AutoFormer.configure_optimizers() should only create/return a scheduler when "
        "self.lr_scheduler_milestones is not None (so users can disable scheduler)."
    )

    # 4) When scheduler enabled, MultiStepLR should use milestones=self.lr_scheduler_milestones
    assert re.search(r"milestones\s*=\s*self\.lr_scheduler_milestones", source), (
        "MultiStepLR should be configured with milestones=self.lr_scheduler_milestones "
        "to respect user-provided milestones."
    )