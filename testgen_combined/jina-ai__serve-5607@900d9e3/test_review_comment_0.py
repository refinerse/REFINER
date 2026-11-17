import re


def test_stream_prefetch_respects_explicit_argument_over_instance_default():
    """
    Functional intent: if `prefetch` is passed explicitly to `stream(...)`, it must be
    used (unless overridden by metadata). The bug in the "before" code resets prefetch
    unconditionally to `self._prefetch`, ignoring the input parameter.

    Since we cannot import the module in this environment (missing aiostream),
    we verify the concrete implementation choice via source inspection.
    """
    source = open("/workspace/jina/serve/stream/__init__.py", "r", encoding="utf-8").read()

    # The fixed implementation must initialize prefetch by combining the explicit
    # argument and the instance default:
    #   prefetch = prefetch or self._prefetch
    assert (
        "prefetch = prefetch or self._prefetch" in source
    ), (
        "RequestStreamer.stream must respect the explicit `prefetch` argument by using "
        "`prefetch = prefetch or self._prefetch`. The implementation that unconditionally "
        "sets `prefetch = self._prefetch` ignores the input parameter."
    )

    # And it must NOT unconditionally overwrite the passed-in parameter.
    # Use a regex to specifically match an assignment statement to self._prefetch.
    assert not re.search(
        r"^\s*prefetch\s*=\s*self\._prefetch\s*$", source, flags=re.MULTILINE
    ), (
        "RequestStreamer.stream should not unconditionally overwrite the `prefetch` "
        "parameter with `self._prefetch`."
    )