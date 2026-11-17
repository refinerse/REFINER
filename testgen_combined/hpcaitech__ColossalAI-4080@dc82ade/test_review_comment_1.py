import re


def test_sltrainer_docstring_no_longer_mentions_train_dataloader_arg():
    """
    The review comment requests that dataloaders should be passed in fit(), not __init__().
    This was fixed by removing 'train_dataloader' from SLTrainer's documented Args list.

    Since importing fails in this environment (missing `coati` package), we inspect source.
    """
    source = open("/workspace/applications/Chat/coati/trainer/base.py", "r", encoding="utf-8").read()

    # Ensure we're checking the SLTrainer docstring block specifically.
    m = re.search(
        r"class\s+SLTrainer\b.*?\"\"\"(.*?)\"\"\"",
        source,
        flags=re.DOTALL,
    )
    assert m is not None, "Could not locate SLTrainer docstring in /workspace/applications/Chat/coati/trainer/base.py"

    doc = m.group(1)

    assert "train_dataloader" not in doc, (
        "SLTrainer docstring still documents 'train_dataloader (DataLoader)' as an __init__ argument. "
        "After the fix, dataloaders should not be documented as SLTrainer __init__ args."
    )