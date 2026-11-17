import re


def test_style_refactor_to_class_and_fixture_and_removed_alternatives_block():
    source_path = "/workspace/conans/test/integration/build_requires/test_build_requires_source_method.py"
    source = open(source_path, encoding="utf-8").read()

    # Style expectation from the review resolution: refactor from a single top-level test
    # function into a pytest class with a fixture for the shared TestClient setup.
    assert (
        "class TestBuildEnvSource" in source
    ), "Expected a pytest test class 'TestBuildEnvSource' (refactor from a single function)."
    assert (
        "@pytest.fixture()" in source and "def client(self):" in source
    ), "Expected a pytest fixture 'client' method inside the test class for shared setup."
    assert (
        "def test_build_requires_source" not in source
    ), "Did not expect legacy top-level 'test_build_requires_source' after style refactor."

    # The before version contained large triple-quoted 'ALTERNATIVE 1..4' blocks that were removed.
    assert (
        "ALTERNATIVE 1" not in source
        and "ALTERNATIVE 2" not in source
        and "ALTERNATIVE 3" not in source
        and "ALTERNATIVE 4" not in source
    ), "Expected old 'ALTERNATIVE 1..4' comment blocks to be removed in the refactored test."

    # Ensure multiple focused tests exist (the after version has several methods).
    tests = re.findall(r"^\s*def\s+(test_[a-zA-Z0-9_]+)\s*\(", source, flags=re.M)
    assert (
        len(tests) >= 4
    ), f"Expected refactor into multiple focused test methods (>=4), found {len(tests)}: {tests}"