"""Config flow for AirMusic Media Player integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any
from urllib.parse import urlparse

from .airmusic import (
    AIRMUSIC,
    ConnectionError as FSConnectionError,
    InvalidPinException,
    NotImplementedException,
)
import voluptuous as vol

from homeassistant.components import ssdp
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PIN, CONF_PORT

from .const import (
    CONF_WEBAIRMUSIC_URL,
    DEFAULT_PIN,
    DEFAULT_PORT,
    DOMAIN,
    SSDP_ATTR_SPEAKER_NAME,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)

STEP_DEVICE_CONFIG_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_PIN,
            default=DEFAULT_PIN,
        ): str,
    }
)


def hostname_from_url(url: str) -> str:
    """Return the hostname from a url."""
    return str(urlparse(url).hostname)
