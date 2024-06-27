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
)
from homeassistant.const import STATE_IDLE, STATE_PLAYING, STATE_PAUSED, CONF_HOST  # Add this import

from .airmusic import airmusic
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_AIRMUSIC = (
    SUPPORT_PLAY | SUPPORT_PAUSE | SUPPORT_STOP | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | SUPPORT_SELECT_SOURCE
)

SOURCES = {
    "FM Radio": airmusic.KEY_MODE,
    "DAB+ Radio": airmusic.KEY_MODE,
    "Internet Radio": airmusic.KEY_INTERNETRADIO,
    "AUX": airmusic.KEY_MODE,
    "Network Device": airmusic.KEY_MODE,
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the AirMusic media player platform."""
    if discovery_info is None:
        return

    ip_address = hass.data[DOMAIN][CONF_HOST]

    async_add_entities([AirMusicDevice(ip_address)])

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirMusic from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    ip_address = config[CONF_HOST]

    async_add_entities([AirMusicDevice(ip_address)])

class AirMusicDevice(MediaPlayerEntity):
    """Representation of an AirMusic device."""

    def __init__(self, ip_address):
        self._ip_address = ip_address
        self._state = STATE_IDLE
        self._volume = 0
        self._muted = False
        self._source = None
        self._airmusic = airmusic(ip_address)

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
    def source_list(self):
        return list(SOURCES.keys())

    def update(self):
        try:
            status = self._airmusic.get_status()
            self._state = STATE_PLAYING if status == 'playing' else STATE_IDLE
            self._volume = self._airmusic.get_volume() / 100
            self._muted = self._airmusic.is_muted()
        except Exception as e:
            _LOGGER.error(f"Error updating AirMusic device: {e}")

    def media_play(self):
        if self._airmusic.play():
            self._state = STATE_PLAYING

    def media_pause(self):
        if self._airmusic.pause():
            self._state = STATE_PAUSED

    def media_stop(self):
        if self._airmusic.stop():
            self._state = STATE_IDLE

    def set_volume_level(self, volume):
        if self._airmusic.set_volume(int(volume * 100)):
            self._volume = volume

    def mute_volume(self, mute):
        if self._airmusic.mute(mute):
            self._muted = mute

    def select_source(self, source):
        if source in SOURCES:
            if self._airmusic.press_key(SOURCES[source])):
                self._source = source

