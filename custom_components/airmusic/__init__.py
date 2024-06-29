import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the AirMusic component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    devices = conf.get('devices', [])

    hass.data.setdefault(DOMAIN, {})

    for device in devices:
        ip_address = device.get(CONF_HOST)
        name = device.get(CONF_NAME)

        hass.data[DOMAIN][ip_address] = {
            CONF_HOST: ip_address,
            CONF_NAME: name,
        }

        await hass.async_create_task(
            discovery.async_load_platform(hass, 'media_player', DOMAIN, {
                CONF_HOST: ip_address,
                CONF_NAME: name,
            }, config)
        )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up AirMusic from a config entry."""
    _LOGGER.debug(f"Setting up entry: {entry.data}")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setup(entry, 'media_player')
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading entry: {entry.entry_id}")
    await hass.config_entries.async_forward_entry_unload(entry, 'media_player')
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
