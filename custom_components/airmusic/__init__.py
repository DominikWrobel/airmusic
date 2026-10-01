"""Set up AirMusic config entries and apply station options without a reload."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HOST, CONF_NAME, SUPPORTED_DOMAINS
from .stations import CONF_STATIONS, DEFAULT_STATIONS


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if CONF_STATIONS not in entry.options:
        hass.config_entries.async_update_entry(entry, options={
            **entry.options, CONF_STATIONS: [dict(s) for s in DEFAULT_STATIONS]})
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_DOMAINS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    success = await hass.config_entries.async_unload_platforms(entry, SUPPORTED_DOMAINS)
    if success:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return success


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    entity = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if entity:
        if entity._host != entry.data[CONF_HOST] or entity._name != entry.data[CONF_NAME]:
            await hass.config_entries.async_reload(entry.entry_id)
            return
        entity.update_station_options(entry.options.get(CONF_STATIONS, []))
        await entity.async_update()
        entity.async_write_ha_state()


