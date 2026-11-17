import re


def test_audio_decode_mp3_uses_path_or_file_parameter_name():
    """
    Review comment requested a clearer parameter name like `path_or_buf`.
    The merged code renamed `_decode_example_with_torchaudio(self, value)` to `_decode_mp3(self, path_or_file)`.
    This test enforces that runtime-visible refactor at the source level.
    """
    source = open("/workspace/src/datasets/features/audio.py", "r", encoding="utf-8").read()

    # Must have the new helper method with an explicit "path_or_file" parameter name
    assert re.search(r"def\s+_decode_mp3\s*\(\s*self\s*,\s*path_or_file\s*\)\s*:", source), (
        "Expected Audio to define `_decode_mp3(self, path_or_file)` (parameter renamed from generic `value`), "
        "as requested in the review comment."
    )

    # And torchaudio.load should use that parameter (not the old `value` symbol)
    assert "torchaudio.load(path_or_file" in source, (
        "Expected `_decode_mp3` to pass `path_or_file` into `torchaudio.load(...)`."
    )