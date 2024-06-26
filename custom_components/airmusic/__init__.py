"""
Support for Lenco DIR150BK and other Airmusic based Internet Radios.
"""
import json
import time
import airmusic

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PIN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_WEBAIRMUSIC_URL, DOMAIN

PLATFORMS = [Platform.MEDIA_PLAYER]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AirMusic from a config entry."""

    webairmusic_url = entry.data[CONF_WEBAIRMUSIC_URL]
    pin = entry.data[CONF_PIN]

    airmusic = AIRMUSIC(webairmusic_url, pin)

    try:
        await airmusic.get_power()
    except FSConnectionError as exception:
        raise ConfigEntryNotReady from exception

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = airmusic

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok





