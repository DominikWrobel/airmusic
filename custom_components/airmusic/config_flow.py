from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

class AirMusicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AirMusic."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="AirMusic", data=user_input)

        data_schema = {
            vol.Required("ip_address"): str,
            vol.Required("token"): str
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )
