import re


def test_travis_flake8_not_run_twice():
    source = open("/workspace/bin/test_travis.sh", "r", encoding="utf-8").read()

    # The review comment indicates that running both:
    #   flake8 sympy;
    #   flake8 --doctests ... sympy;
    # would run normal flake8 checking twice. The fix is to avoid the second
    # flake8 invocation with --doctests in this script.
    assert "--doctests" not in source, (
        "bin/test_travis.sh should not invoke flake8 with --doctests because it "
        "causes normal flake8 checks to run twice. Remove the 'flake8 --doctests ...' "
        "line from the TEST_FLAKE8 block."
    )

    # Additional guard: there should be exactly one flake8 invocation in the file.
    flake8_cmds = [
        line for line in source.splitlines()
        if re.search(r"(^|\s)flake8(\s|;|$)", line) and not line.lstrip().startswith("#")
    ]
    assert len(flake8_cmds) == 1, (
        f"Expected exactly 1 flake8 invocation in bin/test_travis.sh, found {len(flake8_cmds)}: "
        f"{flake8_cmds}"
    )