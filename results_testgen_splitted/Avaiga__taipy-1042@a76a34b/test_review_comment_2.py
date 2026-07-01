import re


def test_scenario_config_does_not_set_instance_specific_fields_name_and_tags():
    """
    Style rule from review: scenario 'name' and 'tags' are instance-specific and must not be passed
    to Config.configure_scenario(...). They should be provided/tagged at scenario creation time.
    """
    source = open("/workspace/tests/core/test_taipy.py", "r", encoding="utf-8").read()

    # Look for any Config.configure_scenario(...) call that explicitly passes name= or tags=.
    # This is intentionally simple source-level enforcement because it's a test-code style change.
    pattern = re.compile(r"Config\.configure_scenario\([^)]*\b(name|tags)\s*=", re.DOTALL)
    bad_calls = pattern.findall(source)

    assert (
        not bad_calls
    ), "tests/core/test_taipy.py should not pass instance-specific 'name' or 'tags' to Config.configure_scenario()."