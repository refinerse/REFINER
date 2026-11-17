import re


def test_psutil_is_imported_unconditionally_and_no_skipif_guard():
    """
    Style requirement: psutil is a hard requirement for the test suite, so
    tests should import it directly and not guard with try/except ImportError
    or define HAS_PSUTIL with a skipif.
    """
    path = "/workspace/tests/pytests/integration/daemons/test_memory_leak.py"
    source = open(path, "r", encoding="utf-8").read()

    # Must have a direct psutil import (after version: `import psutil`)
    assert re.search(r"(?m)^\s*import\s+psutil\s*$", source), (
        "Expected an unconditional `import psutil` statement."
    )

    # Must NOT use guarded import pattern
    assert not re.search(
        r"(?ms)^\s*try:\s*\n(?:.*\n)*?\s*import\s+psutil\s*\n(?:.*\n)*?\s*except\s+ImportError\s*:",
        source,
    ), "psutil import should not be wrapped in try/except ImportError."

    # Must NOT define HAS_PSUTIL or skip based on it
    assert "HAS_PSUTIL" not in source, (
        "Found HAS_PSUTIL; since psutil is required, this guard should be removed."
    )
    assert "pytest.mark.skipif" not in source, (
        "Found pytest.mark.skipif; the test should not conditionally skip due to psutil."
    )