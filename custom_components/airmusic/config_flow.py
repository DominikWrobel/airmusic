"""Configure a radio and manage station names/artwork in Home Assistant."""
import xml.etree.ElementTree as ET

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_HOST, CONF_NAME, DEFAULT_NAME, DEFAULT_USERNAME, DEFAULT_PASSWORD
from .stations import CONF_STATIONS, DEFAULT_STATIONS, validate_station
from .transport import RadioTransport



def device_schema(values):
    return vol.Schema({
        vol.Required(CONF_HOST, default=values.get(CONF_HOST, '')): str,
        vol.Required(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
    })


async def validate_device(hass, host):
    transport = RadioTransport(hass, host, aiohttp.BasicAuth(DEFAULT_USERNAME, DEFAULT_PASSWORD))
    try:
        content = await transport.request('GET', f'http://{host}/playinfo')
        if not content:
            return 'cannot_connect'
        try:
            ET.fromstring(content)
        except ET.ParseError:
            return 'invalid_response'
        if 'INVALID_CMD' in content:
            content = await transport.request('GET', f'http://{host}/init?language=en')
            if not content or 'INVALID_CMD' in content or 'FAIL' in content:
                return 'init_failed'
        return None
    finally:
        await transport.close()


class AirMusicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            # Expect an IP / hostname, not an URL or path.
            if not host or any(c in host for c in '/?#:@ '):
                errors['base'] = 'invalid_host'
            else:
                error = await validate_device(self.hass, host)
                if error:
                    errors['base'] = error
                else:
                    name = user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME
                    return self.async_create_entry(title=name, data={CONF_HOST: host, CONF_NAME: name})
        return self.async_show_form(step_id='user', data_schema=device_schema(user_input or {}), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        # Current HA injects the read-only config_entry property.
        return AirMusicOptionsFlow()


class AirMusicOptionsFlow(config_entries.OptionsFlow):
    """Each station is edited in ordinary text fields, without JSON/YAML."""

    def __init__(self):
        self._stations = None
        self._edit_index = None

    def _load_stations(self):
        if self._stations is None:
            self._stations = [dict(s) for s in self.config_entry.options.get(CONF_STATIONS, DEFAULT_STATIONS)]

    async def async_step_init(self, user_input=None):
        self._load_stations()
        return self.async_show_menu(step_id='init', menu_options=['add_station', 'edit_station', 'delete_station', 'device'])

    async def async_step_add_station(self, user_input=None):
        self._load_stations()
        self._edit_index = None
        return await self._station_form('add_station', user_input)

    def _selection_schema(self):
        options = [{'value': str(i), 'label': f"{s['name']} — {s.get('pattern') or s['name']}"}
                   for i, s in enumerate(self._stations)]
        return vol.Schema({vol.Required('station'): selector.SelectSelector(
            selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN))})

    async def async_step_edit_station(self, user_input=None):
        self._load_stations()
        if not self._stations:
            return self.async_abort(reason='no_stations')
        if user_input is not None:
            self._edit_index = int(user_input['station'])
            return await self.async_step_station()
        return self.async_show_form(step_id='edit_station', data_schema=self._selection_schema())

    async def async_step_station(self, user_input=None):
        return await self._station_form('station', user_input)

    async def _station_form(self, step_id, user_input):
        errors = {}
        if user_input is not None:
            try:
                station = validate_station(user_input, self._stations, self._edit_index)
            except ValueError as err:
                errors['base'] = str(err)
            else:
                if self._edit_index is None:
                    self._stations.append(station)
                else:
                    self._stations[self._edit_index] = station
                return self._save()
        values = user_input if user_input is not None else (
            self._stations[self._edit_index] if self._edit_index is not None else {})
        schema = vol.Schema({
            vol.Optional('pattern', default=values.get('pattern', '')): str,
            vol.Required('name', default=values.get('name', '')): str,
            vol.Optional('logo', default=values.get('logo', '')): str,
        })
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def async_step_delete_station(self, user_input=None):
        self._load_stations()
        if not self._stations:
            return self.async_abort(reason='no_stations')
        if user_input is not None:
            self._stations.pop(int(user_input['station']))
            return self._save()
        return self.async_show_form(step_id='delete_station', data_schema=self._selection_schema())

    def _save(self):
        return self.async_create_entry(title='', data={**self.config_entry.options, CONF_STATIONS: self._stations})

    async def async_step_device(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if not host or any(c in host for c in '/?#:@ '):
                errors['base'] = 'invalid_host'
            else:
                error = await validate_device(self.hass, host)
                if error:
                    errors['base'] = error
                else:
                    name = user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, title=name,
                        data={**self.config_entry.data, CONF_HOST: host, CONF_NAME: name})
                    return self._save()
        return self.async_show_form(step_id='device',
            data_schema=device_schema(user_input or self.config_entry.data), errors=errors)
