import re

def test_commented_train_valid_device_moves_removed():
    source = open("/workspace/examples/pytorch/graphsage/node_classification.py", "r", encoding="utf-8").read()

    # The review asked to remove commented-out lines; author reverted.
    # Ensure there are no commented-out `.to(device)` lines for train/valid indices.
    commented_train = re.search(r"(?m)^\s*#\s*train_idx\s*=\s*train_idx\.to\(\s*device\s*\)\s*$", source)
    commented_valid = re.search(r"(?m)^\s*#\s*valid_idx\s*=\s*valid_idx\.to\(\s*device\s*\)\s*$", source)

    assert commented_train is None and commented_valid is None, (
        "Expected the commented-out lines moving train_idx/valid_idx to device to be removed "
        "(no lines like `#train_idx = train_idx.to(device)` / `#valid_idx = valid_idx.to(device)`), "
        "but at least one is still present in examples/pytorch/graphsage/node_classification.py."
    )

    # Also assert the lines are present uncommented (the 'reverted' outcome).
    uncommented_train = re.search(r"(?m)^\s*train_idx\s*=\s*train_idx\.to\(\s*device\s*\)\s*$", source)
    uncommented_valid = re.search(r"(?m)^\s*valid_idx\s*=\s*valid_idx\.to\(\s*device\s*\)\s*$", source)

    assert uncommented_train and uncommented_valid, (
        "Expected `train_idx = train_idx.to(device)` and `valid_idx = valid_idx.to(device)` to exist "
        "as active (uncommented) code after the revert."
    )