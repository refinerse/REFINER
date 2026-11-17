import re


def test_quickstart_exec_examples_include_cpu_and_gpu_commands():
    source_path = "/workspace/docs/source/getting-started/quickstart.rst"
    source = open(source_path, "r", encoding="utf-8").read()

    # The reviewed change ensures the quickstart shows both CPU and GPU training
    # commands, with explicit GPU allocation using --gpus=V100:1.
    assert (
        "$ sky exec mycluster python train_cpu.py" in source
    ), (
        "Quickstart should show a CPU training example command:\n"
        "  $ sky exec mycluster python train_cpu.py\n"
        f"File: {source_path}"
    )
    assert (
        "$ sky exec mycluster --gpus=V100:1 python train_gpu.py" in source
    ), (
        "Quickstart should show a GPU training example command with explicit "
        "GPU allocation:\n"
        "  $ sky exec mycluster --gpus=V100:1 python train_gpu.py\n"
        f"File: {source_path}"
    )

    # Guard against the regressed/incorrect single example that doesn't request GPUs.
    assert "$ sky exec mycluster python train.py" not in source, (
        "Quickstart should not only show a generic training command without GPU "
        "allocation (regression from the review fix):\n"
        "  $ sky exec mycluster python train.py\n"
        f"File: {source_path}"
    )

    # Also ensure the two commands appear as distinct console lines (format check).
    assert re.search(
        r"(?m)^\s*\$\s+sky exec mycluster python train_cpu\.py\s*$", source
    ), f"CPU command should appear as its own console line in {source_path}"
    assert re.search(
        r"(?m)^\s*\$\s+sky exec mycluster --gpus=V100:1 python train_gpu\.py\s*$",
        source,
    ), f"GPU command should appear as its own console line in {source_path}"