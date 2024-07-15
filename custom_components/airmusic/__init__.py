"""
Support for Airmusic Internet Radios.
"""

import logging
import urllib.parse
import urllib.request
import aiohttp
import asyncio
import voluptuous as vol

from homeassistant.const import (
    CONF_DEVICES, CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_TIMEOUT,
    CONF_USERNAME)
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_HOST, CONF_NAME

_LOGGER = logging.getLogger(__name__)

# VERSION
VERSION = '1.2'

# REQUIREMENTS
REQUIREMENTS = ['beautifulsoup4==4.6.3']

# LOGGING
_LOGGER = logging.getLogger(__name__)

# DOMAIN
# DOMAIN = 'airmusic'

# Supported domains
SUPPORTED_DOMAINS = ['media_player']

# DEFAULTS
DEFAULT_PORT = 8080
DEFAULT_NAME = "Airmusic Radio"
DEFAULT_TIMEOUT = 50
DEFAULT_USERNAME = 'roosu3g4go6sk7'
DEFAULT_PASSWORD = 'ji39454xu/^'
DEFAULT_SOURCE = ''
DEFAULT_IMAGE = 'logo'

# Local
CONF_SOURCE = 'source'
CONF_IMAGE = 'image'
CONF_OPENER = ''

AIRMUSIC_CONFIG = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.socket_timeout,
    vol.Optional(CONF_SOURCE, default=DEFAULT_SOURCE): cv.string,
    vol.Optional(CONF_IMAGE, default=DEFAULT_IMAGE): cv.string,
    })


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICES):
            vol.All(cv.ensure_list, [
                vol.Schema({
                    vol.Required(CONF_HOST): cv.string,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                    vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME):
                        cv.string,
                    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD):
                        cv.string,
                    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT):
                        cv.socket_timeout,
                    vol.Optional(CONF_SOURCE, default=DEFAULT_SOURCE):
                        cv.string,
                    vol.Optional(CONF_IMAGE, default=DEFAULT_IMAGE):
                        cv.string,
                }),
            ]),
        })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Airmusic component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    _LOGGER.info("Initializing Airmusic devices from YAML configuration")

    airmusic_list = []

    configured_devices = config[DOMAIN].get(CONF_DEVICES, [])
    for device in configured_devices:
        airmusic = AirmusicDevice(
            device.get(CONF_HOST),
            device.get(CONF_PORT),
            device.get(CONF_NAME),
            device.get(CONF_USERNAME),
            device.get(CONF_PASSWORD),
            device.get(CONF_TIMEOUT),
            device.get(CONF_SOURCE),
            device.get(CONF_IMAGE)
        )

        _LOGGER.debug("Airmusic device %s configured", device.get(CONF_HOST))
        airmusic_list.append(airmusic)

    hass.data[DOMAIN] = airmusic_list

    if not airmusic_list:
        _LOGGER.info("No Airmusic devices configured")
        return False

    _LOGGER.debug("Configured %s Airmusic devices", len(airmusic_list))

    for domain in SUPPORTED_DOMAINS:
        hass.async_create_task(
            discovery.async_load_platform(hass, domain, DOMAIN, {}, config)
        )
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Airmusic from a config entry."""
    _LOGGER.info("Setting up Airmusic from config entry")

    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]

    airmusic = AirmusicDevice(host, None, name, None, None, None, None, None)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = airmusic

    _LOGGER.debug("Airmusic device %s set up from config entry", host)

    for domain in SUPPORTED_DOMAINS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, domain)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    _LOGGER.info("Unloading Airmusic config entry")

    hass.data[DOMAIN].pop(entry.entry_id)

    for domain in SUPPORTED_DOMAINS:
        await hass.config_entries.async_forward_entry_unload(entry, domain)

    return True

class AirmusicDevice(Entity):
    """Representation of a Airmusic device."""

    def __init__(self, host, port, name, username, password, timeout,
                image, source):
        """Initialize the Airmusic device."""
        self._host = host
        self._port = port
        self._name = name
        self._username = username
        self._password = password
        self._timeout = timeout
        self._source = source
        self._image = image
        self._pwstate = False
        self._volume = 0
        self._muted = False
        self._selected_source = ''
        self._image_url = {}
        self._source_names = {}
        self._sources = {}
        # Opener for http connection
        self._opener = aiohttp.ClientSession()

    @property
    def get_host(self):
        """Return the host of the device."""
        return self._host

    @property
    def get_port(self):
        """Return the port of the device."""
        return self._port

    @property
    def get_name(self):
        """Return the name of the device."""
        return self._name

    @property
    def get_username(self):
        """Return the username of the device."""
        return self._username

    @property
    def get_password(self):
        """Return the password of the device."""
        return self._password

    @property
    def get_timeout(self):
        """Return the timeout of the device."""
        return self._timeout

    @property
    def get_source(self):
        """Return the favorites of the device."""
        return self._source

    @property
    def get_image(self):
        """Return the image of the device."""
        return self._image

    @property
    def get_opener(self):
        """Return the socket of the device."""
        return self._opener


