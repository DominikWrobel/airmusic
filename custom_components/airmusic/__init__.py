import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

DOMAIN = 'airmusic'
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the AirMusic component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    ip_address = conf.get('ip_address')
    token = conf.get('token')

    hass.data[DOMAIN] = {
        'ip_address': ip_address,
        'token': token
    }

    await discovery.async_load_platform(hass, 'media_player', DOMAIN, {}, config)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up AirMusic from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, 'media_player')
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, 'media_player')
    hass.data[DOMAIN].pop(entry.entry_id)

    return True





