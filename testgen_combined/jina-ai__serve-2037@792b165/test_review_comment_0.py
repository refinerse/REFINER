import re


def test_hubio_build_uses_basename_for_dockerfile_when_path_may_be_relative():
    """
    Regression test for hub builds with relative args.path:
    build() must pass only the dockerfile filename (basename) to docker SDK,
    not an absolute/relative path returned by _check_completeness().
    """
    source = open("/workspace/jina/docker/hubio.py", "r", encoding="utf-8").read()

    # Ensure build() derives dockerfile value via os.path.basename(...)
    assert (
        "os.path.basename(_check_result['Dockerfile'])" in source
        or 'os.path.basename(_check_result["Dockerfile"])' in source
    ), (
        "HubIO.build() should pass only the basename of the Docker"
        "file returned from _check_completeness(), e.g. "
        "os.path.basename(_check_result['Dockerfile']). This prevents docker SDK "
        "from incorrectly joining relative `path` with a relative/absolute dockerfile path."
    )

    # And ensure it actually passes that basename variable into docker build calls.
    # We keep this flexible and purely string-based to avoid fragile parsing.
    assert re.search(r"dockerfile\s*=\s*_dockerfile\b", source), (
        "HubIO.build() should pass dockerfile=_dockerfile to the docker build calls. "
        "This variable should be computed via os.path.basename(...) to work when args.path is relative."
    )

    # Negative check: the old buggy behavior passed the full path.
    assert not re.search(r"dockerfile\s*=\s*_dockerfile_path\b", source), (
        "HubIO.build() must not pass dockerfile=_dockerfile_path (full path). "
        "Passing a path can break builds when args.path is a relative path."
    )