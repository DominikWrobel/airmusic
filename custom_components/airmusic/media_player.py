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
from homeassistant.const import STATE_IDLE, STATE_PLAYING, STATE_PAUSED

from .airmusic import airmusic

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

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the AirMusic media player platform."""
    if discovery_info is None:
        return

    ip_address = hass.data['airmusic']['ip_address']
    token = hass.data['airmusic']['token']

    add_entities([AirMusicDevice(ip_address, token)])

class AirMusicDevice(MediaPlayerEntity):
    """Representation of an AirMusic device."""

    def __init__(self, ip_address, token):
        """Initialize the AirMusic device."""
        self._ip_address = ip_address
        self._token = token
        self._state = STATE_IDLE
        self._volume = 0
        self._muted = False
        self._source = None
        self._airmusic = airmusic(ip_address)

    @property
    def name(self):
        """Return the name of the device."""
        return "AirMusic"

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_AIRMUSIC

    @property
    def source(self):
        """Return the current source."""
        return self._source

    @property
    def source_list(self):
        """List of available input sources."""
        return list(SOURCES.keys())

    def update(self):
        """Fetch new state data for this media player."""
        status = self._airmusic.get_status()
        self._state = STATE_PLAYING if status == 'playing' else STATE_IDLE
        self._volume = self._airmusic.get_volume() / 100
        self._muted = self._airmusic.is_muted()
        # Assuming there's a way to get the current source, set self._source accordingly

    def media_play(self):
        """Send play command."""
        self._airmusic.play()
        self._state = STATE_PLAYING

    def media_pause(self):
        """Send pause command."""
        self._airmusic.pause()
        self._state = STATE_PAUSED

    def media_stop(self):
        """Send stop command."""
        self._airmusic.stop()
        self._state = STATE_IDLE

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._airmusic.set_volume(int(volume * 100))
        self._volume = volume

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        self._airmusic.mute(mute)
        self._muted = mute

    def select_source(self, source):
        """Select input source."""
        if source in SOURCES:
            self._airmusic.press_key(SOURCES[source])
            self._source = source

