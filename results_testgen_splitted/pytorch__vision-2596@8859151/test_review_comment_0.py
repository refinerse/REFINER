import re


def test_ffmpeg_version_pinning_is_consistent_with_downloaded_artifacts():
    source = open("/workspace/packaging/pkg_helpers.bash", "r", encoding="utf-8").read()

    # The structural change requested: don't have an unpinned conda install for ffmpeg
    # while also downloading a pinned tarball. We assert that within download_copy_ffmpeg(),
    # any active `conda install ... ffmpeg` line must pin a version (e.g., ffmpeg=4.2).
    func_match = re.search(r"(?ms)^\s*download_copy_ffmpeg\(\)\s*\{.*?^\s*\}\s*$", source)
    assert func_match, "Expected to find download_copy_ffmpeg() function definition in /workspace/packaging/pkg_helpers.bash"
    body = func_match.group(0)

    active_conda_ffmpeg_installs = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "conda install" in stripped and re.search(r"\bffmpeg\b", stripped):
            active_conda_ffmpeg_installs.append(stripped)

    assert active_conda_ffmpeg_installs, (
        "Expected download_copy_ffmpeg() to contain at least one active conda ffmpeg installation line "
        "(or to explicitly disable it). If it was removed entirely, adjust this test to the new structure."
    )

    unpinned = [
        ln
        for ln in active_conda_ffmpeg_installs
        # matches 'ffmpeg' not immediately followed by '=<version>'
        if re.search(r"\bffmpeg\b(?!\s*=)", ln)
    ]
    assert not unpinned, (
        "Found unpinned conda ffmpeg install(s) inside download_copy_ffmpeg(), which is structurally "
        "inconsistent when the script downloads a pinned ffmpeg tarball. "
        "Pin ffmpeg in conda install (e.g., 'ffmpeg=4.2') or disable/remove the unpinned install line(s). "
        f"Unpinned line(s): {unpinned}"
    )