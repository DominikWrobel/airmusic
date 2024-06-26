import logging
from homeassistant.helpers import discovery

DOMAIN = 'airmusic'
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
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





