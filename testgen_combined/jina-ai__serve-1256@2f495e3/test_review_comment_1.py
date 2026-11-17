import re


def test_grpc_channel_fstring_d_format_removed():
    source = open("/workspace/jina/clients/python/grpc.py", "r", encoding="utf-8").read()

    # This style change removes the redundant integer formatting code `:d`
    # inside the f-string used to build the "host:port" channel target.
    assert ":d" not in source, (
        "Expected redundant f-string integer format specifier ':d' to be removed "
        "from jina/clients/python/grpc.py (e.g. f'{args.host}:{args.port_expose}' "
        "instead of f'{args.host}:{args.port_expose:d}'). Found ':d' in file."
    )

    # Ensure the intended f-string target format is present (host:port).
    assert re.search(r"f'\{args\.host\}:\{args\.port_expose\}'", source), (
        "Expected grpc channel target to use f-string without ':d': "
        "f'{args.host}:{args.port_expose}'. Pattern not found."
    )