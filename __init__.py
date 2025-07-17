"""The Dune Weaver integration."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .const import DOMAIN
from .coordinator import setup_table_service

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dune Weaver from a config entry."""
    await setup_table_service(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.BUTTON])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, f"run_random_pattern_{entry.entry_id}")
    hass.services.async_remove(DOMAIN, f"run_fitting_pattern_{entry.entry_id}")
    
    return await hass.config_entries.async_forward_entry_unloads(entry, [Platform.BUTTON])
