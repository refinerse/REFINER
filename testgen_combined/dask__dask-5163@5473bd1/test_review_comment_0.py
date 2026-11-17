import re


def test_scheduler_section_awaits_same_scheduler_instance():
    source = open("/workspace/docs/source/setup/python-advanced.rst", encoding="utf-8").read()

    # Isolate ONLY the first python code block that appears in the "Scheduler" section.
    # Stop at the next ".. code-block:: python" to avoid capturing later blocks in the doc.
    m = re.search(
        r"(?ms)^Scheduler\s*\n-+\s*\n.*?^\.\. code-block:: python\s*\n(?P<block>(?:^[ \t]+.*\n)+?)(?=^\.\. code-block:: python|^\S|\Z)",
        source,
    )
    assert m, "Could not locate the first python code block in the 'Scheduler' section."

    block = m.group("block")

    assert "s = Scheduler()" in block, (
        "Expected the first Scheduler example to construct the scheduler with 's = Scheduler()'."
    )
    assert "s = await s" in block, (
        "Expected the first Scheduler example to await the same instance it constructed "
        "('s = await s'), rather than constructing a different Scheduler in the await line."
    )
    assert "s = await Scheduler()" not in block, (
        "The first Scheduler example should not use 's = await Scheduler()' after creating "
        "'s = Scheduler()', since that would await a different Scheduler instance."
    )