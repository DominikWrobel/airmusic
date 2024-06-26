# custom_components/airmusic/media_player.py

import logging
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.components.media_player.const import (
    SUPPORT_PLAY,
    SUPPORT_PAUSE,
    SUPPORT_STOP,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_NEXT_TRACK,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_IDLE,
    STATE_PLAYING,
)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

SUPPORT_AIRMUSIC = (
    SUPPORT_PLAY
    | SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
)

DEFAULT_NAME = "AirMusic"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the AirMusic platform."""
    if discovery_info is None:
        return

    host = discovery_info[CONF_HOST]
    name = discovery_info.get(CONF_NAME, DEFAULT_NAME)

    add_entities([AirMusicDevice(name, host)], True)


class AirMusicDevice(MediaPlayerEntity):
    """Representation of an AirMusic device."""

    def __init__(self, name, host):
        """Initialize the AirMusic device."""
        self._name = name
        self._host = host
        self._state = STATE_IDLE
        self._volume_level = 0.5
        self._is_muted = False

        # Initialization of the device with provided script
        # self._device = YourProvidedScript(host)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Return the volume level of the device."""
        return self._volume_level

    @property
    def is_volume_muted(self):
        """Return true if the device is muted."""
        return self._is_muted

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_AIRMUSIC

    def turn_on(self):
        """Turn on the media player."""
        _LOGGER.debug("Turning on the player")
        self._state = STATE_PLAYING
        self.schedule_update_ha_state()

    def turn_off(self):
        """Turn off the media player."""
        _LOGGER.debug("Turning off the player")
        self._state = STATE_IDLE
        self.schedule_update_ha_state()

    def set_volume_level(self, volume):
        """Set the volume level."""
        _LOGGER.debug("Setting volume to %s", volume)
        self._volume_level = volume
        # self._device.set_volume(volume)
        self.schedule_update_ha_state()

    def mute_volume(self, mute):
        """Mute the volume."""
        _LOGGER.debug("Muting volume: %s", mute)
        self._is_muted = mute
        # self._device.mute(mute)
        self.schedule_update_ha_state()

    def media_play(self):
        """Send play command."""
        _LOGGER.debug("Playing media")
        self._state = STATE_PLAYING
        # self._device.play()
        self.schedule_update_ha_state()

    def media_pause(self):
        """Send pause command."""
        _LOGGER.debug("Pausing media")
        self._state = STATE_IDLE
        # self._device.pause()
        self.schedule_update_ha_state()

    def media_stop(self):
        """Send stop command."""
        _LOGGER.debug("Stopping media")
        self._state = STATE_IDLE
        # self._device.stop()
        self.schedule_update_ha_state()

    def media_previous_track(self):
        """Send previous track command."""
        _LOGGER.debug("Playing previous track")
        # self._device.previous_track()
        self.schedule_update_ha_state()

    def media_next_track(self):
        """Send next track command."""
        _LOGGER.debug("Playing next track")
        # self._device.next_track()
        self.schedule_update_ha_state()
