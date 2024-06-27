import logging
import requests
import xmltodict

_LOGGER = logging.getLogger(__name__)

class airmusic:
    # Define the constants
    KEY_MODE = 'KEY_MODE'
    KEY_INTERNETRADIO = 'KEY_INTERNETRADIO'
    KEY_PLAY = 'KEY_PLAY'
    KEY_PAUSE = 'KEY_PAUSE'
    KEY_STOP = 'KEY_STOP'
    KEY_MUTE = 'KEY_MUTE'
    KEY_UNMUTE = 'KEY_UNMUTE'

    DEFAULT_AUTH = 'c3UzZzRnbzZzazc6amkzOTQ1NHh1L14='

    def __init__(self, device_address, timeout=5):
        self._device_address = device_address
        self._timeout = timeout

    def press_key(self, key):
        url = f"http://{self._device_address}/command"
        headers = {
            "Authorization": f"Basic {self.DEFAULT_AUTH}"
        }
        payload = f"<?xml version='1.0'?><key code='{key}'/>"
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=self._timeout)
            response.raise_for_status()
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error pressing key {key}: {e}")
            return False

    def get_status(self):
        url = f"http://{self._device_address}/status"
        headers = {
            "Authorization": f"Basic {self.DEFAULT_AUTH}"
        }
        try:
            response = requests.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            status = xmltodict.parse(response.content)
            return status['status']['state']
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error getting status: {e}")
            return None

    def get_volume(self):
        url = f"http://{self._device_address}/volume"
        headers = {
            "Authorization": f"Basic {self.DEFAULT_AUTH}"
        }
        try:
            response = requests.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            volume = xmltodict.parse(response.content)
            return int(volume['volume']['level'])
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error getting volume: {e}")
            return 0

    def is_muted(self):
        url = f"http://{self._device_address}/mute"
        headers = {
            "Authorization": f"Basic {self.DEFAULT_AUTH}"
        }
        try:
            response = requests.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            mute_status = xmltodict.parse(response.content)
            return mute_status['mute']['status'] == 'true'
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error getting mute status: {e}")
            return False

    def play(self):
        return self.press_key(self.KEY_PLAY)

    def pause(self):
        return self.press_key(self.KEY_PAUSE)

    def stop(self):
        return self.press_key(self.KEY_STOP)

    def set_volume(self, volume):
        url = f"http://{self._device_address}/volume"
        headers = {
            "Authorization": f"Basic {self.DEFAULT_AUTH}"
        }
        payload = f"<?xml version='1.0'?><volume>{volume}</volume>"
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=self._timeout)
            response.raise_for_status()
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error setting volume: {e}")
            return False

    def mute(self, mute):
        return self.press_key(self.KEY_MUTE if mute else self.KEY_UNMUTE)
