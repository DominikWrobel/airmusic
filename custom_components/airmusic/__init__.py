# custom_components/airmusic/__init__.py

import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, HomeAssistantType
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME

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

async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
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
        discovery.async_load_platform(hass, "media_player", DOMAIN, conf, config)
    )

    return True

# Uncomment and implement if there is an async_setup_entry
# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Set up AirMusic from a config entry."""
#     _LOGGER.info("Setting up AirMusic from config entry")
#     return await async_setup(hass, entry.data)

# Uncomment and implement if there is an async_unload_entry
# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Unload a config entry."""
#     _LOGGER.info("Unloading AirMusic config entry")
#     return True
