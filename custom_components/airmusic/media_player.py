import logging
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerDeviceClass,
    MediaPlayerState,
)
from homeassistant.components.media_player.const import (
    SUPPORT_PLAY,
    SUPPORT_PAUSE,
    SUPPORT_STOP,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_BROWSE_MEDIA
)
from homeassistant.const import STATE_OFF, STATE_IDLE, STATE_PLAYING, STATE_PAUSED, CONF_HOST  # Import CONF_HOST

from .airmusicapi import airmusic
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_AIRMUSIC = (
    SUPPORT_PLAY | SUPPORT_PAUSE | SUPPORT_STOP | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | SUPPORT_SELECT_SOURCE | SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_PLAY_MEDIA | SUPPORT_BROWSE_MEDIA
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

    ip_address = hass.data[DOMAIN][CONF_HOST]

    async_add_entities([AirMusicDevice(hass, ip_address)])

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirMusic from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    ip_address = config[CONF_HOST]

    async_add_entities([AirMusicDevice(hass, ip_address)])

class AirMusicDevice(MediaPlayerEntity):
    """Representation of an AirMusic device."""

    def __init__(self, hass, ip_address):
        self._hass = hass
        self._ip_address = ip_address
        self._state = STATE_OFF
        self._volume = 0
        self._muted = False
        self._source = None
        self._airmusic = airmusic(ip_address, timeout = 10)
        self._turn_off = self.turn_off
        self._turn_on = self.turn_on
        self._stop = self.stop
        self._pause = self.pause

    @property
    def name(self):
        return "AirMusic"

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

    @property
    def turn_on(self):
        return self._turn_on
        
    @property
    def turn_off(self):
        return self._turn_off
        
    @property
    def stop(self):
        return self._stop

    @property
    def pause(self):
        return self._pause


    @property
    def source_list(self):
        return list(SOURCES.keys())
        
    async def async_update(self):
        try:
            self._state = await self._hass.async_add_executor_job(self._airmusic.get_playinfo)
            self._state = STATE_PLAYING if self._state.get("sid") != 6 else STATE_PAUSED if self._state.get("sid") != 9 else STATE_IDLE
            self._muted = await self._hass.async_add_executor_job(self._airmusic.get_mute)
            self._volume = await self._hass.async_add_executor_job(self._airmusic.get_volume) / 30
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

#  def media_play(self):
#        if self._state.get("sid") != 6:
#            self._state = STATE_PLAYING

#    def media_pause(self):
#        if self._state.get("sid") != 9:
#            self._state = STATE_PAUSED

#    def media_stop(self):
#        if self._state.get("sid") != 1:
#            self._state = STATE_IDLE

#    async def async_media_play(self):
#        if await self._hass.async_add_executor_job(self._airmusic.play):
#            self._state = STATE_PLAYING

#    async def async_media_pause(self):
#       if await self._hass.async_add_executor_job(self._airmusic.pause):
#            self._state = STATE_PAUSED

#    async def async_media_stop(self):
#        if await self._hass.async_add_executor_job(self._airmusic.stop):
#            self._state = STATE_IDLE

    async def async_set_volume_level(self, volume):
        if await self._hass.async_add_executor_job(self._airmusic.set_volume, int (volume * 30)):
            self._volume = volume

    def mute_volume(self, mute):
        self._airmusic.mute = mute
        
    def stop (self, stop):
        self._airmusic.stop = stop
        
    def turn_on(self, turn_on):
        self._airmusic.turn_on = turn_on

    def turn_off(self, turn_off):
        self._airmusic.turn_off = turn_off
        
    def pause (self, pause):
        self._aimusic.pause = pause

    async def async_select_source(self, source):
        if source in SOURCES:
            if await self._hass.async_add_executor_job(self._airmusic.press_key, SOURCES[source]):
                self._source = source
