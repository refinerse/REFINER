import re


def test_dispatch_data_checks_num_ips_equals_num_parts():
    """
    The review comment asks for a check that the number of partitions equals
    the number of IPs. We verify the implementation exists in tools/dispatch_data.py
    by inspecting the source, since importing the module fails in this environment.
    """
    source = open("/workspace/tools/dispatch_data.py", "r", encoding="utf-8").read()

    # Look for logic that counts lines in ip_config and asserts equality with num_parts.
    # This is the key behavior added after the review.
    has_ip_config_open = "with open(args.ip_config" in source or "open(args.ip_config" in source
    has_readlines_count = "readlines()" in source and ("len(f.readlines())" in source or "len(" in source)
    has_assert_num_ips_equals_num_parts = re.search(
        r"assert\s+num_ips\s*==\s*num_parts", source
    ) is not None

    assert has_ip_config_open and has_readlines_count and has_assert_num_ips_equals_num_parts, (
        "dispatch_data.py must validate that the number of IPs (lines in args.ip_config) "
        "equals the number of partitions (num_parts), e.g., by counting lines and asserting "
        "'num_ips == num_parts'. This check is missing."
    )