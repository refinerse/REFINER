import re


def test_create_importable_file_helper_added_to_deduplicate_logic():
    """
    Functional intent of the review comment: extract repeated "create importable module" logic into a helper.

    We can't import src.datasets.load in this environment, so we verify via source inspection that:
    - the new helper `_create_importable_file` exists (after)
    - canonical + local factories use `_create_importable_file(` (after)
    This should fail on the before version where factories inline the repeated logic and no helper exists.
    """
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    assert "def _create_importable_file(" in source, (
        "Expected refactor to introduce helper `def _create_importable_file(...)` in /workspace/src/datasets/load.py "
        "to reduce repeated 'importable module creation' code across factories."
    )

    # Ensure the helper is actually used (not just defined).
    # Require multiple call sites to reflect deduplication across factories.
    call_sites = len(re.findall(r"\b_create_importable_file\s*\(", source))
    assert call_sites >= 3, (
        "Expected `_create_importable_file(` to be used in multiple factories (canonical/local/metric) "
        f"to eliminate repeated code; found {call_sites} call site(s)."
    )