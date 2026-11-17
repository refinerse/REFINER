import asyncio
import logging

from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.script import DATA_SCRIPTS, Script


def test_disabled_subscript_is_skipped_for_sequence_and_logs_generic_message(caplog):
    """Disabled non-top-level scripts must be skipped in _ScriptRun._async_run_script.

    This must apply to sequence sub-scripts too (not only parallel), and the log
    message must be generic (must not mention "parallel").
    """

    async def _run() -> list[str]:
        logger = logging.getLogger(
            "homeassistant.helpers.script.test_disabled_sequence"
        )
        logger.setLevel(logging.DEBUG)

        hass = HomeAssistant(".")
        await hass.async_start()
        try:
            # Avoid cross-test interference
            hass.data[DATA_SCRIPTS] = []

            parent = Script(
                hass,
                sequence=[{"sequence": []}],  # a step that creates a sequence sub-script
                name="parent",
                domain="test",
                top_level=True,
                logger=logger,
            )

            # Create the non-top-level sequence script and disable it
            sub = await parent._async_get_sequence_script(0)  # noqa: SLF001
            sub.enabled = False

            caplog.set_level(logging.INFO)
            await parent.async_run(context=Context())

            return [
                rec.getMessage()
                for rec in caplog.records
                if rec.name == logger.name and rec.levelno == logging.INFO
            ]
        finally:
            await hass.async_stop()

    messages = asyncio.run(_run())

    assert any(
        "Skipping disabled script:" in msg for msg in messages
    ), (
        "Expected a generic 'Skipping disabled script: <name>' log message when a "
        "disabled non-top-level sub-script (created by a sequence action) is encountered. "
        "This indicates the enabled check is in _async_run_script and applies to sequence "
        "sub-scripts, not only parallel."
    )

    assert not any("Skipping disabled parallel script:" in msg for msg in messages), (
        "Log message should be generic and must not mention 'parallel'. "
        "The enabled check should not be tied specifically to parallel execution."
    )