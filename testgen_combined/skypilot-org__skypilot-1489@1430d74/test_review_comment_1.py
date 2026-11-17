import re


def _read_config_v2_source() -> str:
    # The file moved/renamed in the "after" version. Support both locations.
    candidates = [
        "/workspace/sky/skylet/providers/aws/config_v2.py",  # before location
        "/workspace/sky/skylet/providers/aws/config.py",     # after location
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            continue
    raise AssertionError(
        "Could not find AWS config source file. Tried: "
        + ", ".join(candidates)
        + ". The test expects the repo to contain either config_v2.py (before) "
        "or config.py (after)."
    )


def test_skypilot_constant_simplified_name():
    source = _read_config_v2_source()

    # The review change: simplify SKYPILOT value from "skypilot-service" to "skypilot".
    assert re.search(r'^\s*SKYPILOT\s*=\s*["\']skypilot["\']\s*$', source, re.M), (
        "Expected SKYPILOT constant to be simplified to 'skypilot' "
        "(e.g., SKYPILOT = 'skypilot')."
    )
    assert "skypilot-service" not in source, (
        "Did not expect legacy value 'skypilot-service' to remain after "
        "simplification to 'skypilot'."
    )