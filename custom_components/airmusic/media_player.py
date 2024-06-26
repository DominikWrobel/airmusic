class AirMusicDevice(MediaPlayerEntity):
    """Representation of an AirMusic device."""

    def __init__(self, ip_address, token):
        self._ip_address = ip_address
        self._token = token
        self._state = STATE_IDLE
        self._volume = 0
        self._muted = False
        self._source = None
        self._airmusic = airmusic(ip_address)

    def update(self):
        try:
            status = self._airmusic.get_status()
            self._state = STATE_PLAYING if status == 'playing' else STATE_IDLE
            self._volume = self._airmusic.get_volume() / 100
            self._muted = self._airmusic.is_muted()
            # Assuming there's a way to get the current source, set self._source accordingly
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
            if self._airmusic.press_key(SOURCES[source]):
                self._source = source
