import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
import aiohttp
import xml.etree.ElementTree as ET

from .const import DOMAIN, CONF_HOST, CONF_NAME, DEFAULT_NAME

DEFAULT_USERNAME = 'su3g4go6sk7'
DEFAULT_PASSWORD = 'ji39454xu/^'

class AirMusicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            # Validate the connection to the host with authentication
            session = aiohttp_client.async_get_clientsession(self.hass)
            url = f"http://{host}/playinfo"
            try:
                async with session.get(url, auth=aiohttp.BasicAuth(DEFAULT_USERNAME, DEFAULT_PASSWORD)) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        rt_element = root.find('rt')
                        if rt_element is not None and rt_element.text == 'INVALID_CMD':
                            # Initialize the device
                            init_url = f"http://{host}/init"
                            async with session.get(init_url, auth=aiohttp.BasicAuth(DEFAULT_USERNAME, DEFAULT_PASSWORD)) as init_response:
                                if init_response.status != 200:
                                    errors["base"] = "init_failed"
                                    return self.async_show_form(
                                        step_id="user", data_schema=self.data_schema, errors=errors
                                    )
                        # Proceed with the configuration
                        return self.async_create_entry(title=name, data={CONF_HOST: host, CONF_NAME: name})
                    else:
                        errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except ET.ParseError:
                errors["base"] = "invalid_response"
            except Exception:
                errors["base"] = "unknown"

        self.data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("name", default=DEFAULT_NAME): str
        })

        return self.async_show_form(
            step_id="user", data_schema=self.data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AirMusicOptionsFlow(config_entry)


class AirMusicOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            # Validate the connection to the host with authentication
            session = aiohttp_client.async_get_clientsession(self.hass)
            url = f"http://{host}/playinfo"
            try:
                async with session.get(url, auth=aiohttp.BasicAuth(DEFAULT_USERNAME, DEFAULT_PASSWORD)) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        rt_element = root.find('rt')
                        if rt_element is not None and rt_element.text == 'INVALID_CMD':
                            # Initialize the device
                            init_url = f"http://{host}/init"
                            async with session.get(init_url, auth=aiohttp.BasicAuth(DEFAULT_USERNAME, DEFAULT_PASSWORD)) as init_response:
                                if init_response.status != 200:
                                    errors["base"] = "init_failed"
                                    return self.async_show_form(
                                        step_id="user", data_schema=self.data_schema, errors=errors
                                    )
                        # Proceed with updating the configuration
                        self.hass.config_entries.async_update_entry(
                            self.config_entry, data={CONF_HOST: host, CONF_NAME: name}
                        )
                        return self.async_create_entry(title="", data={})
                    else:
                        errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except ET.ParseError:
                errors["base"] = "invalid_response"
            except Exception:
                errors["base"] = "unknown"

        self.data_schema = vol.Schema({
            vol.Required(CONF_HOST, default=self.config_entry.data.get(CONF_HOST)): str,
            vol.Optional(CONF_NAME, default=self.config_entry.data.get(CONF_NAME, DEFAULT_NAME)): str
        })

        return self.async_show_form(
            step_id="user", data_schema=self.data_schema, errors=errors
        )

