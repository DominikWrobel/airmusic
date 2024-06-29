import logging
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerDeviceClass,
    MediaPlayerState,
)
from homeassistant.components.media_player.const import (
    SUPPORT_PLAY,
    SUPPORT_STOP,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_BROWSE_MEDIA
)
from homeassistant.const import STATE_ON, STATE_OFF, STATE_IDLE, STATE_PLAYING, STATE_PAUSED, CONF_HOST, CONF_NAME  # Import CONF_HOST

from .airmusicapi import airmusic
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_AIRMUSIC = (
    SUPPORT_PLAY | SUPPORT_STOP | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | SUPPORT_SELECT_SOURCE | SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_PLAY_MEDIA | SUPPORT_BROWSE_MEDIA
)

SOURCES = {
#    "FM Radio": airmusic.KEY_MODE,
#    "DAB+ Radio": airmusic.KEY_MODE,
    "Internet Radio": airmusic.KEY_INTERNETRADIO,
    "AUX": airmusic.KEY_MODE,
    "Network Device": airmusic.KEY_MODE,
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the AirMusic media player platform."""
    if discovery_info is None:
        return

    ip_address = discovery_info[CONF_HOST]
    name = discovery_info[CONF_NAME]

    async_add_entities([AirMusicDevice(hass, ip_address, name)], update_before_add=True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirMusic from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    ip_address = config[CONF_HOST]

    async_add_entities([AirMusicDevice(hass, ip_address)], update_before_add=True)

class AirMusicDevice(MediaPlayerEntity):
    """Representation of an AirMusic device."""

    def __init__(self, hass, ip_address, name):
        self._hass = hass
        self._ip_address = ip_address
        self._name = name
        self._state = STATE_OFF
        self._volume = 0
        self._muted = False
        self._source = None
        self._airmusic = airmusic(ip_address, timeout = 10)
        self._status = {}
        self._media_image_url = f"http://{ip_address}:8080/playlogo.jpg"

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def volume_level(self):
        return self._volume

    @property
    def is_volume_muted(self):
        return self._muted

    @property
    def supported_features(self):
        return SUPPORT_AIRMUSIC

    @property
    def source(self):
        return self._source

#    @property
#    def turn_on(self):
#        return self._turn_on
        
#    @property
#    def turn_off(self):
#        return self._turn_off
        
    @property
    def stop(self):
        return self._stop

    @property
    def play_pause(self):
        return self._play_pause


    @property
    def source_list(self):
        return list(SOURCES.keys())

    @property
    def media_image_url(self):
        """Return the image URL of the currently playing media."""
        return self._media_image_url if self._state == STATE_ON else None
        
    async def async_update(self):
        try:
            self._status = await self._hass.async_add_executor_job(self._airmusic.get_background_play_status)
#            self._state = STATE_PLAYING if self._status.get("sid") == 6 else STATE_IDLE
            self._muted = await self._hass.async_add_executor_job(self._airmusic.get_mute)
            volume_str = await self._hass.async_add_executor_job(self._airmusic.get_volume)
            self._volume = int(volume_str) / 30 
        except Exception as e:
            _LOGGER.error(f"Error updating AirMusic device: {e}")

#    async def async_update(self):
#        try:
#            status = await self._hass.async_add_executor_job(self._airmusic.get_status)
#            self._state = STATE_PLAYING if status == 'playing' else STATE_IDLE
#            self._volume = await self._hass.async_add_executor_job(self._airmusic.get_volume) / 100
#            self._muted = await self._hass.async_add_executor_job(self._airmusic.get_mute())
#        except Exception as e:
#            _LOGGER.error(f"Error updating AirMusic device: {e}")

#    async def media_play(self):
#        if await self._status.get("sid") == 6:
#            self._airmusic.play_pause()
#            self._state = STATE_PLAYING

#    async def media_pause(self):
#        if await self._status.get("sid") == 9:
#            self._airmusic.play_pause()
#            self._state = STATE_PAUSED

#    async def media_stop(self):
#        if await self._status.get("sid") == 1:
#            self._airmusic.play_pause()
#            self._state = STATE_IDLE

    async def media_play(self):
        self._status = await self._hass.async_add_executor_job(self._airmusic.get_background_play_status)
        if self._status.get("sid") == 6:
            await self._hass.async_add_executor_job(self._airmusic.play_pause)
            self._state = STATE_PLAYING

    async def media_pause(self):
        self._status = await self._hass.async_add_executor_job(self._airmusic.get_background_play_status)
        if self._status.get("sid") == 9:
            await self._hass.async_add_executor_job(self._airmusic.play_pause)
            self._state = STATE_PAUSED

    async def media_stop(self):
        self._status = await self._hass.async_add_executor_job(self._airmusic.get_background_play_status)
        if self._status.get("sid") == 1:
            await self._hass.async_add_executor_job(self._airmusic.play_pause)
            self._state = STATE_IDLE

    async def async_set_volume_level(self, volume):
        if await self._hass.async_add_executor_job(self._airmusic.set_volume, int (volume * 30)):
            self._volume = volume

    def mute_volume(self, mute):
        self._airmusic.mute = mute
        
    def stop (self, stop):
        self._airmusic.stop = stop
        
    async def async_turn_on(self):
        await self._hass.async_add_executor_job(self._airmusic.send_rc_key, 7)
        self._state = STATE_ON

    async def async_turn_off(self):
        await self._hass.async_add_executor_job(self._airmusic.send_rc_key, 7)
        self._state = STATE_OFF

#    def turn_on(self, turn_on):
#        self._airmusic.send_rc_key(7)

#    def turn_off(self, turn_off):
#        self._airmusic.send_rc_key(7)
        
    def play_pause (self, play_pause):
        self._aimusic.play_pause = play_pause

    async def async_select_source(self, source):
        if source in SOURCES:
            if await self._hass.async_add_executor_job(self._airmusic.press_key, SOURCES[source]):
                self._source = source
