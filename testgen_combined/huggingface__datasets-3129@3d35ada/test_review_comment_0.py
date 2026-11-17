import re


def test_audio_decode_uses_xopen_and_mp3_accepts_file_like_and_format_arg():
    """
    This test enforces the review-requested behavior/clarity:
    - Non-mp3 path-like decoding should not use bare `open(...)` (it should use `xopen`).
    - MP3 decoding should accept a path or a file-like object, and pass `format="mp3"` to torchaudio.load.

    We rely on source inspection because importing fails in this environment due to pyarrow API mismatch.
    """
    source = open("/workspace/src/datasets/features/audio.py", "r", encoding="utf-8").read()

    # 1) Ensure xopen is used for non-mp3 path-like decoding (instead of open()).
    assert "from ..utils.streaming_download_manager import xopen" in source, (
        "Audio decoding should import and use `xopen` for path-like inputs "
        "(enables streaming/archived files and avoids bare `open`)."
    )
    assert re.search(r"with\s+xopen\(", source), (
        "Expected Audio non-mp3 path-like decoding to use `with xopen(path, 'rb') as f:` "
        "instead of calling `open(path, ...)` directly."
    )
    assert "with open(" not in source, (
        "Audio decoding should not use bare `open(...)` for reading audio paths; "
        "it should use `xopen(...)`."
    )

    # 2) Ensure mp3 decoder function makes it explicit that it takes a path or file-like object,
    #    and passes format='mp3' to torchaudio.load (required for file-like objects).
    assert "def _decode_mp3(self, path_or_file):" in source, (
        "Expected a dedicated mp3 decoding function with a clear `path_or_file` parameter "
        "to support both paths and file-like objects."
    )
    assert "torchaudio.load(path_or_file, format=\"mp3\")" in source, (
        "Expected mp3 decoding to call `torchaudio.load(path_or_file, format=\"mp3\")` "
        "so that file-like objects are supported, not `torchaudio.load(value)`."
    )