import re


def _get_function_source(source: str, func_name: str) -> str:
    """
    Extract a function's source by grabbing everything from `def <name>(` up to
    the next top-level `def ` or `if __name__ ==`.
    """
    m = re.search(rf"(?m)^def {re.escape(func_name)}\(", source)
    assert m, f"Could not find function definition for `{func_name}()`."

    start = m.start()
    rest = source[m.end() :]

    m_next = re.search(r"(?m)^(def [a-zA-Z_]\w*\(|if __name__ ==)", rest)
    end = (m.end() + m_next.start()) if m_next else len(source)
    return source[start:end]


def test_device_string_is_converted_to_torch_device_in_augment_and_augment_squad():
    source = open("/workspace/haystack/utils/augment_squad.py", "r", encoding="utf-8").read()

    augment_src = _get_function_source(source, "augment")
    augment_squad_src = _get_function_source(source, "augment_squad")

    assert (
        "device = torch.device(device)" in augment_src
    ), "Expected `augment()` to convert `device` via `device = torch.device(device)` so callers can pass a string device."

    assert (
        "device = torch.device(device)" in augment_squad_src
    ), "Expected `augment_squad()` to convert `device` via `device = torch.device(device)` before calling model.to(device) / load_glove(..., device=device)."