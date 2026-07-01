import re


def test_sft_trainer_removed_abnormal_loss_warning_check():
    """
    Structural review change: remove the "abnormal loss" warning block from _train.

    Before (should fail this test): contained
        if loss >= 2.5 and is_rank_0():
            self.logger.warning(...)
    After (should pass): this block is removed.
    """
    source = open("/workspace/applications/Chat/coati/trainer/sft.py", "r", encoding="utf-8").read()

    # Look for the specific structural pattern that was removed.
    pattern = re.compile(r"if\s+loss\s*>=\s*2\.5\s+and\s+is_rank_0\(\)\s*:", re.MULTILINE)

    assert not pattern.search(source), (
        "SFTTrainer._train still contains the 'abnormal loss' warning guard "
        "(`if loss >= 2.5 and is_rank_0():`). The review requested removing this."
    )