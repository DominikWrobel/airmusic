# custom_components/airmusic/__init__.py

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_NAME
from . import airmusic


_LOGGER = logging.getLogger(__name__)

DOMAIN = "airmusic"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_NAME, default="AirMusic"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the AirMusic component."""
    _LOGGER.info("Setting up AirMusic component")
    
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    host = conf[CONF_HOST]
    name = conf[CONF_NAME]

    # Pass configuration to the platform
    hass.data[DOMAIN] = conf

    # Load platforms supported by this component
    hass.async_create_task(
        discovery.async_load_platform(hass, "media_player", DOMAIN, {}, config)
    )

    return True
