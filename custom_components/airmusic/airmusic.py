import logging
import requests
import xmltodict
from functools import partial

_LOGGER = logging.getLogger(__name__)

class airmusic:
    # Define the constants
    KEY_HOME = 1
    KEY_UP = 2
    KEY_DOWN = 3
    KEY_LEFT = 4
    KEY_RIGHT = 5
    KEY_ENTER = 6
    KEY_POWER = 7  # Toggle power on/off.
    KEY_MUTE = 8
    KEY_VOLUP = 9  # Volume up one step.
    KEY_VOLDOWN = 10  # Volume down one step.
    KEY_ALARMCLOCK = 11
    KEY_SLEEPTIMER = 12
    KEY_LANGUAGE = 13  # Open the language menu.
    KEY_SCREENDIM = 14  # Toggle screen dim on/off.
    KEY_CHANNELFAV = 15  # Show the favourites menu.
    KEY_BUTTON0 = 17
    KEY_BUTTON1 = 18
    KEY_BUTTON2 = 19
    KEY_BUTTON3 = 20
    KEY_BUTTON4 = 21
    KEY_BUTTON5 = 22
    KEY_BUTTON6 = 23
    KEY_BUTTON7 = 24
    KEY_BUTTON8 = 25
    KEY_BUTTON9 = 26
    KEY_MODE = 28  # Toggle between the device modes: FM, IRadio, USB, AUX, UPNP, ...
    KEY_STOP = 30  # Stop playing a song / station.
    KEY_NEXT = 31  # Go to the next item.
    KEY_PREV = 32  # Go to the next item.
    KEY_USB = 36  # Swith to USB mode.
    KEY_INTERNETRADIO = 40  # Switch to IRadio mode.
    KEY_POWERSAVING = 105  # Go to the power saving menu, item 'Turn On'.
    KEY_EQ_FLAT = 106  # Select "Flat" equaliser mode.
    KEY_SYSTEMMENU = 110  # Go to the system menu.
    KEY_WPS = 111  # Start WPS mode.
    KEY_NEXTFAV = 112  # Go to the next station in the favourites list.

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
        url = f"http://{self._device_address}/init"
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
