# This repository may have environment-level pytest options injected (e.g. via
# PYTEST_ADDOPTS) which can break execution when running with `-c /dev/null`.
# Ensure our test is self-contained by stripping those options.
import os

os.environ.pop("PYTEST_ADDOPTS", None)

import inspect


def test_usermessage_init_docstring_mentions_output_channel_used_to_send_responses():
    import rasa.core.channels.channel as channel

    doc = inspect.getdoc(channel.UserMessage.__init__)
    assert doc is not None, "Expected UserMessage.__init__ to have a docstring."

    expected = (
        "output_channel: the output channel which should be used to send "
        "bot responses back to the user."
    )
    assert expected in doc, (
        "UserMessage.__init__ docstring should explain that 'output_channel' is used to "
        "send bot responses back to the user.\n"
        f"Missing expected line:\n{expected}\n\n"
        f"Actual docstring:\n{doc}"
    )