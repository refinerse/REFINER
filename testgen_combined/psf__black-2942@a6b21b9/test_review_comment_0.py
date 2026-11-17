from black import Mode
from black.mode import Preview
from src.black.lines import Line


def _mode_with_preview_feature(feature: Preview) -> Mode:
    """
    Build a Mode that enables a specific Preview feature in a way that works
    across Black versions (constructor signature changes over time).
    """
    # In these versions, Mode supports `preview` and `enabled_features`.
    return Mode(preview=True, enabled_features={feature})


def test_magic_trailing_comma_disabled_for_single_element_subscript_general() -> None:
    code = "x = a[b,]\n"

    # The behavior under test is guarded by a Preview flag.
    #
    # Before: the relevant flag/behavior was tied to one_tuple_type + annotations,
    #         so this should still return True (magic trailing comma).
    # After:  Preview.one_element_subscript disables magic trailing comma here,
    #         so this should return False.
    mode = _mode_with_preview_feature(getattr(Preview, "one_element_subscript"))
    line = Line(mode=mode)

    for leaf in line.bracket_tracker.visit(code):
        line.append(leaf)

    closing = line.leaves[-1]
    assert closing.value == "]", "Sanity check: expected the last leaf to be the closing ']'"

    assert (
        line.has_magic_trailing_comma(closing) is False
    ), (
        "Expected Black to *not* treat a trailing comma inside a single-element "
        "subscript as magic when the relevant preview feature is enabled "
        "(e.g. `a[b,]`)."
    )