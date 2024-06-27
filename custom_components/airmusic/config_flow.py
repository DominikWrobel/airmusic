from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging

from homeassistant.const import CONF_HOST  # Add this import
from .const import DOMAIN
from .airmusic import airmusic

_LOGGER = logging.getLogger(__name__)

class AirMusicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AirMusic."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Perform a test connection to the AirMusic device
                device = airmusic(user_input[CONF_HOST])
                if not device.get_status():
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(title="AirMusic", data=user_input)
            except Exception as e:
                _LOGGER.error(f"Error during configuration: {e}")
                errors["base"] = "unknown"

        data_schema = {
            vol.Required(CONF_HOST): str
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

