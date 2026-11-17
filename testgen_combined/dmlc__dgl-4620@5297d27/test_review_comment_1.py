import re


def test_dispatch_data_uses_partition_meta_json_for_num_parts_and_verifies_ip_config():
    source = open("/workspace/tools/dispatch_data.py", "r", encoding="utf-8").read()

    # Core behavior change: num_parts should be retrieved from a meta file in partitions-dir
    # (instead of always requiring --num-parts / defaulting to num_chunks).
    assert "partition_meta.json" in source, (
        "dispatch_data.py should look for 'partition_meta.json' under --partitions-dir to "
        "retrieve num_parts and avoid requiring repetitive CLI args."
    )

    assert re.search(r"\bload_partition_meta\b", source), (
        "dispatch_data.py should call load_partition_meta(...) to load num_parts from the "
        "partition meta JSON file."
    )

    # Additional behavior added in the 'after' code: ensure ip_config line count matches num_parts.
    assert "verify ip_config" in source or "num_ips" in source, (
        "dispatch_data.py should verify that the number of lines in --ip-config equals num_parts "
        "(as derived from partition_meta.json when present)."
    )