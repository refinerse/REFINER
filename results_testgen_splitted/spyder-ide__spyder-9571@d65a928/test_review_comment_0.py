import re


def test_zh_cn_translation_percent_placeholders_are_ascii_percent():
    """
    Ensure Chinese translation strings that correspond to msgids using Python
    %-format placeholders don't accidentally use the fullwidth percent sign '％'
    in msgstr placeholders, which breaks runtime formatting.

    This test targets the specific entry from the review hunk.
    """
    po_path = "/workspace/spyder/locale/zh_CN/LC_MESSAGES/spyder.po"
    with open(po_path, "r", encoding="utf-8") as f:
        source = f.read()

    msgid_text = (
        "Decide how graphics are going to be displayed in the console. If unsure, "
        "please select <b>%s</b> to put graphics inside the console or <b>%s</b> to "
        "interact with them (through zooming and panning) in a separate window."
    )

    # Parse msgid/msgstr blocks in a minimal way.
    block_re = re.compile(
        r'msgid\s*""\s*\n(?P<id>(?:".*"\s*\n)+)\s*msgstr\s*""\s*\n(?P<str>(?:".*"\s*\n)+)',
        re.MULTILINE,
    )

    def unquote_po_multiline(block: str) -> str:
        # Extract the inside of each quoted line and join them.
        parts = re.findall(r'"(.*)"', block)
        return "".join(parts).replace(r"\"", '"').replace(r"\n", "\n").replace(r"\\", "\\")

    found_msgstr = None
    for m in block_re.finditer(source):
        mid = unquote_po_multiline(m.group("id"))
        if mid == msgid_text:
            found_msgstr = unquote_po_multiline(m.group("str"))
            break

    assert found_msgstr is not None, (
        "Could not find the expected msgid/msgstr entry for the IPython console "
        "graphics backend description in /workspace/spyder/locale/zh_CN/LC_MESSAGES/spyder.po"
    )

    assert "％s" not in found_msgstr, (
        "The zh_CN translation for the graphics backend description contains a "
        "fullwidth percent placeholder '％s'. It must use the ASCII placeholder '%s' "
        "so Python %-formatting works at runtime."
    )
    assert found_msgstr.count("%s") == 2, (
        "The zh_CN translation for the graphics backend description must contain "
        "exactly two ASCII '%s' placeholders to match the msgid placeholders."
    )