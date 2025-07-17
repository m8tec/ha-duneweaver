import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up DuneWeaver buttons from a config entry."""
    async_add_entities([
        DuneWeaverRandomPatternButton(entry),
        DuneWeaverFittingPatternButton(entry)
    ])

class DuneWeaverRandomPatternButton(ButtonEntity):
    """Representation of a DuneWeaver button to run a random pattern."""

    def __init__(self, entry: ConfigEntry):
        self._attr_name = f"Run Random Pattern ({entry.title})"
        self._attr_unique_id = f"duneweaver_{entry.entry_id}_run_random"
        self._entry = entry

    async def async_press(self) -> None:
        _LOGGER.info("'Run Random Pattern' button pressed. Calling service.")
        await self.hass.services.async_call(
            DOMAIN,
            f"run_random_pattern_{self._entry.entry_id}",
            blocking=False,
        )

class DuneWeaverFittingPatternButton(ButtonEntity):
    """Representation of a DuneWeaver button to run a fitting pattern."""

    def __init__(self, entry: ConfigEntry):
        self._attr_name = f"Run Fitting Pattern ({entry.title})"
        self._attr_unique_id = f"duneweaver_{entry.entry_id}_run_fitting"
        self._entry = entry

    async def async_press(self) -> None:
        _LOGGER.info("'Run Fitting Pattern' button pressed. Calling service.")
        await self.hass.services.async_call(
            DOMAIN,
            f"run_fitting_pattern_{self._entry.entry_id}",
            blocking=False,
        )
