import re


def test_default_log_json_level_key_is_level_not_severity():
    source = open("/workspace/openhands/core/logger.py", "r", encoding="utf-8").read()

    # Find the assignment to LOG_JSON_LEVEL_KEY and extract the default value used in os.getenv(..., <default>)
    m = re.search(
        r"^LOG_JSON_LEVEL_KEY\s*=\s*os\.getenv\(\s*['\"]LOG_JSON_LEVEL_KEY['\"]\s*,\s*['\"](?P<default>[^'\"]+)['\"]\s*\)",
        source,
        flags=re.MULTILINE,
    )
    assert m, (
        "Expected openhands/core/logger.py to define LOG_JSON_LEVEL_KEY via "
        "os.getenv('LOG_JSON_LEVEL_KEY', <default>)"
    )

    default = m.group("default")
    assert default == "level", (
        "LOG_JSON_LEVEL_KEY default should be 'level' (so JSON logs use the conventional 'level' field) "
        f"but found default {default!r}. This change should be reverted."
    )