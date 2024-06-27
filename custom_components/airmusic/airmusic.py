"""
Support for Lenco DIR150BK and other Airmusic based Internet Radios.
"""
import logging
import requests
import xmltodict

_LOGGER = logging.getLogger(__name__)

VERSION = '0.0.1'


class airmusic(object):
    """
    This class contains constants ands methods to implement the AirMusic API.
    """

    # The KEY_... constants represent the corresponding key of the InfraRed Remote.
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

    SID = {1, 'Stopped',
           2, 'Buffering',
           6, 'Playing',
           7, 'Ending',
           9, 'Paused',
           12, 'Reading from file',
           14, 'failed to connect', }

    def __init__(self, device_address, timeout=5):
        """!
        Constructor of the Airmusic API class.
        @param device_address holds the device IP-address or resolvable name.
        @param timeout determines the maximum amount of seconds to wait for a reply from the device.
        """
        self.device_address = CONF_HOST
        self.timeout = timeout
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s',
                            filename=('airmusic-debug.log'),)
        self.logger = logging.getLogger("airmusic")
        # Will be updated after successful call to init() command.
        self.language = None
        self.hotkey_fav = None
        self.push_talk = None
        self.play_mode = None
        self.sw_update = None

    def __del__(self):
        """!
        @private
        Finalise the communication with the device by closing the session.
        """
        self.logger = None  # No logging possible at termination.
        self.stop()
        self.send_cmd('exit')

    def __repr__(self):
        """!
        @private
        Return a string representation of the Airmusic API instance, showing the most important variables.
        """
        ret = ""
        ret += "Airmusic API Ver. {}".format(VERSION)
        ret += "\n  address={}".format(self.device_address)
        ret += "\n  timeout={}".format(self.timeout)
        ret += "\n  language={}".format(self.language)
        ret += "\n  hotkey={}".format(self.hotkey_fav)
        ret += "\n  push_talk={}".format(self.push_talk)
        ret += "\n  play_mode={}".format(self.play_mode)
        ret += "\n  sw_update={}".format(self.sw_update)
        return ret

    def __str__(self):
        """!
        @private
        Return a string representation of the Airmusic API instance, showing the most important variables.
        """
        return self.__repr__()

    def send_cmd(self, cmd, port=80, params=None):
        """!
        Send the command and optional parameters to the device and receive the response.
        Most commands will be sent to port 80, but some might require port 8080.
        There are commands that have no parameters. In that case the params parameter can be omitted.
        In case a command requires additional parameters, these must be passed as a dict().
        For example, the list command has the following syntax:
          http://.../list?id=1&start=1&count=15
        In that case, parameter cmd will be set to 'list', and parameter params will be set to
        the dict(id=1, start=1, count=15).
        @param cmd is the command to send.
        @param port is the http port to send the command to. Default is 80.
        @param params holds the command parameters (as a dict).
        """
        # The parameters for the command, if any, are received in a dict() structure.
        if type(params) is not dict:
            params = dict()
        if self.logger:
            self.logger.debug("Sending: {}".format(cmd))
        # Send the command to the device. The Basic Authentication values are hardcoded.
        result = requests.get('http://{}:{}/{}'.format(self.device_address, port, cmd),
                              auth=('su3g4go6sk7', 'ji39454xu/^'),
                              params=params,
                              timeout=self.timeout)
        if self.logger:
            self.logger.debug("Response: headers={}, text=\"{}\"".format(result.headers, result.text))
        if result.ok:
            if 'html' in result.text:  # Some commands, like set_dname, return an HTML page.
                return dict(result='OK')
            return xmltodict.parse(make_xml(result.text))
        logging.error("Error in request: {} : {}".format(result.status_code, result.reason))
        return None

    # ========================================================================
    # Properties
    # ========================================================================

    # Friendly name
    def get_friendly_name(self):
        """!
        Return the human readable name of the device.
        @note Instead of this function, use the property friendly_name.
        @return the device name (string).
        """
        resp = self.send_cmd('irdevice.xml')
        # <root><device><friendlyName>...</friendlyName></device></root>
        return resp['root']['device']['friendlyName']

    def set_friendly_name(self, value):
        """!
        Assign a human readable name to the device.
        @note Instead of this function, use the property friendly_name.
        @param value the device name (string).
        """
        resp = self.send_cmd('set_dname', params=dict(name=value))
        # <result>OK</result>
        return resp

    friendly_name = property(get_friendly_name, set_friendly_name)

    # log level
    def get_log_level(self, loglevel):
        """!
        Get the actual logging level. See the logging library for level values.
        @note Instead of this function, use the property log_level.
        @return the current log level.
        """
        self.logger.setLevel(loglevel)

    def set_log_level(self, loglevel):
        """!
        Change the logging level. See the logging library for level values.
        Default is logging.INFO level.
        @note Instead of this function, use the property log_level.
        @param loglevel specifies the level at which output to the logger will be activated.
        """
        self.logger.setLevel(loglevel)

    log_level = property(get_log_level, set_log_level)

    # mute
    def get_mute(self):
        """!
        Fetch the mute state.
        @note Instead of this function, use the property mute.
        @return True if the device is muted, False if not muted.
        """
        resp = self.get_background_play_status()
        return True if resp['mute'] == '1' else False

    def set_mute(self, value):
        """!
        Specify mute on or off.
        The device can be muted or unmuted, while not changing the volume level set.
        It returns the tags:
         - vol : to indicate the current volume level.
         - mute : the mute flag; 0=Off 1=On.
        @note Instead of this function, use the property mute.
        @param value True to mute the device, False to unmute.
        @return a dict holding vol and mute.
        """
        resp = self.send_cmd('setvol', params=dict(mute=1 if value else 0))
        return resp['result']

    mute = property(get_mute, set_mute)

    # volume
    def get_volume(self):
        """!
        Fetch the volume level.
        @note Instead of this function, use the property volume.
        @return the volume level (0 .. 15).
        """
        resp = self.get_background_play_status()
        return resp['vol']

    def set_volume(self, value):
        """!
        Specify the volume level.
        The volume of the device can be specified in 16 steps, 0-15.
        It returns the tags:
         - vol : to indicate the current volume level.
         - mute : the mute flag; 0=Off 1=On.
        @note Instead of this function, use the property volume.
        @param value is the volume level to set (0 .. 15).
        @return a dict holding vol and mute.
        """
        resp = self.send_cmd('setvol', params=dict(vol=value))
        return resp['result']

    volume = property(get_volume, set_volume)

    # ========================================================================
    # Public methods
    # ========================================================================

    def init(self, language='en'):
        """!
        Initialize session and select the communication language.
        The GUI on the device will show messages in the selected language.
        The same is valid for the content of specific tags.
        It returns the value of several system parameters, being:
         - id (The ID for the main menu),
         - version (The system version),
         - wifi_set_url (URL to start scanning for APs, but its IP address is wrong!),
         - ptver (date part of the version),
         - hotkey_fav (The key of the choosen station in the hotkey list),
         - push_talk (?),
         - leave_msg (?),
         - leave_msg_ios (?),
         - M7_SUPPORT (Flag to indicate if this device has support for the M7 chipset),
         - SMS_SUPPORT (Flag to indicate if SMS is supported),
         - MKEY_SUPPORT (?),
         - UART_CD (?),
         - PlayMode (Represents the current play mode, eg FM, IRadio, ...),
         - SWUpdate (If there is an update available, most of the time value NO).
        @param language holds the communication language, eg. en, fr, de, nl, ...
        @return a dict holding the system parameters and values.
        """
        resp = self.send_cmd('init', params=dict(language=language))
        # <result><id>1</id><lang>en</lang> ... </result>
        result = resp['result']
        self.language = result['lang']
        self.hotkey_fav = result['hotkey_fav']
        self.push_talk = result['push_talk']
        self.play_mode = result['PlayMode']
        self.sw_update = result['SWUpdate']
        return result

    def get_background_play_status(self):
        """!
        Get the status info of the song / station playing.
        A song or Station can play while the user is navigating in the menus.
        The state of what is playing can be retrieved.
        Returned tags are:
         - sid : ?
         - playtime_left : In hh:mm:ss format.
         - vol : the current volume level
         - mute : the current mute state (0=Unmuted, 1=Muted)
        @return the play status.
        """
        resp = self.send_cmd('background_play_status')
        return resp['result']

    def get_BT_status(self):
        """!
        Get the status of bluetooth.
        The status value indicates if bluetooth is connected, idle, etc.
        Returned tags are:
         - vol : the current volume level
         - mute : the current mute state (0=Unmuted, 1=Muted)
         - Status : the bluetooth status value. Value 2=??, 3=??, 4=??
        @return the bluetooth status.
        """
        resp = self.send_cmd('GetBTStatus')
        return resp['result']

    def get_DAB_hotkeylist(self):
        """!
        Fetch the DAB list of hotkeys.
        It is possible to store multiple DAB stations in the favourites list.
        The first five entries are in the DAB hotkeylist. To fetch the complete list,
        it is required to query with the 'list' command, i.e. with get_menu().
        Returned are the following tags:
         - item_total (The total number of items in the list, i.e. 5),
         - item_return (The amount of items in the list),
         - item (repeated (5) times):
        Each item has the following tags:
         - id (Unique ID that can be used to play this station),
         - status ('emptyfile' indicates the entry is not used, 'file' indicates the entry is valid.),
         - name (Holds the station name, if used. Contains 'empty' or a translation of 'empty' if a
                 different language is active).
        @return On success, a dict of favourite stations; On error, a dict {'error': 'reason'}; else None
        """
        resp = self.send_cmd('DABhotkeylist')
        if 'menu' in resp:
            return resp['menu']
        if 'result' in resp:
            return dict(result=resp['result']['rt'])
        return None

    def get_FM_favourites(self):
        """!
        Get the FM favourites.
        A few FM stations can be marked as FM favourites. The list of FM favourites is returned
        with this function.
        Returned are the following tags:
         - item_total (The total number of items in the list, i.e. 5),
         - item_return (The amount of items in the list),
         - item (repeated (5) times):
        Each item has the following tags:
         - id (Unique ID that can be used to play this station),
         - Freq (The FM station fequency, eg. 87.50).
        @return On success, a dict of favourite FM stations; On error, a dict {'error': 'reason'}; else None
        """
        resp = self.send_cmd('GetFMFAVlist')
        if 'menu' in resp:
            return resp['menu']
        if 'result' in resp:
            return dict(result=resp['result']['rt'])
        return None

    def get_FM_status(self):
        """!
        Get the FM status info.
        The FM status can be retrieved in all modes, but it will contain relevant values only
        if the device is in FM mode.
        Returned tags are:
         - vol : the current volume level.
         - mute : the current mute state (0=Unmuted, 1=Muted).
         - Signal : the signal reception level of the FM station.
         - Sound : indicates MONO or STEREO.
         - Search : is TRUE while FM scanning is active, FALSE if no scanning is performed.
         - Freq : indicates the actual FM frequency, eg. 87.50.
         - RDS : If available, shows RDS info.
        @return the FM status.
        """
        resp = self.send_cmd('GetFMStatus')
        return resp['result']

    def set_FM_manualsearch(self, direction):
        """!
        Start FM station search.
        Start scanning the FM frequencies to find another FM station. The direction (Down, Up) needs
        to be specified.
        Note that the 'Search' tag retrieved via get_FM_status() will be set to 'TRUE' as long
        as searching is in progress. Once a station has been found it will contain 'FALSE'.
        @param direction is the direction to search for the next station, 'down' or 'up'.
        @return the command status ('OK')
        """
        if direction == 'down':
            direction = 'backword'
        elif direction == 'up':
            direction = 'forword'
        else:
            return "Error: direction must be 'down' or 'up'."
        resp = self.send_cmd('SetFMManualsearch', params=dict(direction=direction))
        return resp['result']

    def set_FM_mode(self, mode):
        """!
        Specify FM mono or stereo.
        While listening to an FM radio station, it is possible to choose between MONO or (automatic)
        STEREO mode.
        @param mode is 'mono' to select MONO-mode; 'stereo' to select STEREO-mode.
        @return the command status ('OK')
        """
        resp = self.send_cmd('SetFMMode', params=dict(mode=mode))
        return resp['result']

    def get_hotkeylist(self):
        """!
        Fetch the list of hotkeys.
        It is possible to store multiple stations in the favourites list.
        The first five entries are the hotkeylist. To fetch the complete list,
        it is required to query with the 'list' command.
        Returned are the following tags:
         - item_total (The total number of items in the list, i.e. 5),
         - item_return (The amount of items in the list),
         - item (repeated (5) times):
        Each item has the following tags:
         - id (Unique ID that can be used to play this station),
         - status ('emptyfile' indicates the entry is not used, 'file' indicates the entry is valid.),
         - name (Holds the station name, if used. Contains 'empty' or a translation of 'empty' if a
                 different language is active).
        @return On success, a dict of favourite stations; On error, a dict {'error': 'reason'}; else None
        """
        resp = self.send_cmd('hotkeylist')
        if 'menu' in resp:
            return resp['menu']
        if 'result' in resp:
            return dict(result=resp['result']['rt'])
        return None

    def enter_menu(self, menu_id):
        """!
        Enter the given submenu.
        Menus in the device have a unique menu-ID. The contents of a menu can be retrieved
        in one go or in chunks with the get_menu() function. To enter a menu entry
        (i.e. an menu entry that is marked as status: content), the submenu unique ID is
        needed.
        @param menu_id is the unique menu id of the sub menu to enter.
        @return True on success, False on error; else None
        """
        resp = self.send_cmd('gochild', params=dict(id=menu_id))
        if 'result' in resp:
            new_id = resp['result']['id']
            return new_id == menu_id
        return None

    def get_menu(self, menu_id=1, start=1, count=15):
        """!
        Fetch the list of items in a given menu.
        Menus in the device have a unique menu-ID. The contents of a menu can be retrieved
        in one go or in chunks. The params 'start' and 'count' determine which part of the
        full menu will be retrieved.
        Returned are the following tags:
         - item_total (The total number of items in the menu, eg. 50),
         - item_return (The amount of items returned here, eg. 10),
         - item (a menu entry, repeated (item_return) times):
        Each item has the following tags:
         - id (Unique ID for this menu entry),
         - status ('emptyfile' indicates the entry is not used, 'file' indicates the entry is valid,
                   'content' means there is a sub-menu available.),
         - name (The menu name, if used).
        If retrieving the menu failed, a single dict is returned holding the error reason.
        If no menu was returned by the device, nor an error indication, the function returns None.
        @param menu_id is the unique ID of the menu to retrieve.
        @param start specifies the start index of the list to retrieve.
        @param count specifies the number of entries to fecth.
        @return On success, a dict of menu entries; On error, a dict {'error': 'reason'}; else None
        """
        resp = self.send_cmd('list', params=dict(id=menu_id, start=start, count=count))
        if 'menu' in resp:
            return resp['menu']
        if 'result' in resp:
            return dict(result=resp['result']['error'])
        return None

    def get_playinfo(self):
        """!
        Return information about the song being played.
        Depending on the connection state, it is possible that not all tags are present.
        For instance, while connecting to a radio station the tags vol, mute and status are present,
        but tags artist, song and so on are not.
        When playing a song/station, the following tags are present:
         - vol (Volume, ranges 0 - 15),
         - mute (Mute flag, 0=Off, 1=On),
         - status (Song or connection status message, in the local language (see init() ),
         - sid (?),
         - logo_img (URL to fetch the logo of the station / song),
         - stream_format (Shows for instance 'MP3 /128 Kbps'),
         - station_info (The name of the station, eg ' SLAM'),
         - song (The name of the song),
         - artist (The artist of the song).
        @return A dict with information about the song/station being played.
        """
        resp = self.send_cmd('playinfo')
        if 'vol' in resp['result']:
            return resp['result']
        return dict(result=resp['result'])

    def get_systeminfo(self):
        """!
        Fetch firmware and network info.
        The following tags will be returned:
         - SW_Ver : The firmware identification string
         - wifi_info : Contains several tags related to the wifi connection
             - status : the Wifi connection status
             - MAC : the MAC address of the wifi interface
             - SSID : the name of the AP the device is connected to
             - Signal : the wifi signal level
             - Encryption : indicates the encryption type used
             - IP : the device's IP-address
             - Subnet : the applied subnet mask for IP-adresses
             - Gateway : the default router (gateway)
             - DNS1 : the IP-address of the first Domain Name Server
             - DNS2 : the IP-address of the second DNS
        @return a dict holding the system info.
        """
        resp = self.send_cmd('GetSystemInfo')
        return resp['menu']

    def play_DAB_favourite(self, keynr):
        """!
        Start playing a DAB station from the DAB favourites list.
        The DAB favourites list can be retrieved with get_DAB_hotkeylist().
        This list shows the stored FM stations, each with their own id.
        On return:
         - id (The ID of the menu holding this station),
         - rt (The status text, eg 'OK').
        @param keynr is the id of the DAB station to play.
        @return A dict with the tags id and rt.
        """
        # <result><id>75</id><rt>OK</rt></result>
        resp = self.send_cmd('playDABhotkey', params=dict(key=keynr))
        return resp['result']

    def play_FM_favourite(self, favnr):
        """!
        Start playing an FM station from the FM favourites list.
        The FM favourites list can be retrieved with get_FM_favourites().
        That list shows the stored FM stations, each with their own id.
        The id must be passed to this function to select the FM station.
        On return:
         - the status text, eg 'OK' or 'FAIL'.
        @param favnr is the id of the FM station in the list, value range: 1 - ?.
        @return The status text.
        """
        # <result>OK</result>
        resp = self.send_cmd('GotoFMfav', params=dict(fav=favnr))
        return resp['result']

    def play_hotkey(self, keynr):
        """!
        Start playing a station from the hotkey list.
        The hotkey list is a small list where favourite stations can be stored.
        On the remote control there is a limited set of numbered keys, each representing
        one entry in this list. This function will take the keynr and start to play the
        corresponding favourite station.
        On return:
         - id (The ID of the menu holding this station),
         - rt (The status text, eg 'OK').
        @param keynr is the number of the station, value range: 1 - ?.
        @return A dict with the tags id and rt.
        """
        # <result><id>75</id><rt>OK</rt></result>
        resp = self.send_cmd('playhotkey', params=dict(key=keynr))
        return resp['result']

    def play_pause(self):
        """!
        Play/Pause the current song/station.
        A song (file) or a station is paused playing or unpaused.
        On return:
         - rt (The status text, eg 'OK').
        @return A dict with the tag rt.
        """
        resp = self.send_cmd('PlayOP', params=dict(cmd='PlayPause'))
        return resp['result']

    def play_remotefile(self, url, name=None):
        """!
        Start playing a song from a remote source by means of a URL .
        The device can connect using the URL to a remote device and play the song as
        indicated by the URL.
        To verify if the device can play the URL, just enter that URL in the address bar
        of a browser. If the browser can play the file, the radio device should be able
        to do so as well.
        Example: http://192.168.2.116:8888/local&name=Over_the_Horizon.mp3
        On the Airmusic Control App it is also possible to record a voice message and to play it
        directly on the radio device. In that case the URL is pointing to a file and the app
        also provided the parameter name with value 'Intercom'.
        Example: http://192.168.2.116:8889/msg.wav&name=Intercom
        Note: Make sure you navigate to the top level menu using the back() function until it returns ID=1
        before you start playing remote songs. The device might freeze if you are not at the top level menu.
        On return:
         - rt (The status text, eg 'OK').
        @param url is the URL of the song to play.
        @param name is None if not specified, holds a string to display on the device.
        @return A dict with the tag rt.
        """
        # <result><rt>OK</rt></result>
        params = dict(url=url)
        if name:
            params.update(dict(name=name))
        resp = self.send_cmd('LocalPlay', params=params)
        return resp['result']

    def play_station(self, station_id):
        """!
        Start playing a song or station based on its unique ID.
        The unique song or station ID can be found using the 'get_menu' command. The format is
        something like 75_3. This function will request the radio to play the
        given song or station ID.
        Note: It is required to navigate to the menu that holds the station_id. Failure
              to do so will cause the device to hang. A power cycle is needed to get the
              device remote controllable again!
        On return:
         - id (The ID of the menu containing this song/station),
         - rt (The status text, eg 'OK').
        @param station_id is the unique ID of the song / station to play.
        @return A dict with the tags id and rt.
        """
        # <result><id>75</id><rt>OK</rt></result>
        resp = self.send_cmd('play_stn', params=dict(id=station_id))
        return resp['result']

    def play_url(self, station_id):
        """!
        Fetch the URL for the logo of a song or station based on its unique ID.
        The unique song or station ID can be found using the 'get_menu' command. The format is
        something like 75_3. This function will request the radio to return the URL of the
        logo of the given song or station ID.
        Note: It is required to navigate to the menu that holds the station_id. Failure
              to do so will cause the device to hang. A power cycle is needed to get the
              device remote controllable again!
        On return:
         - url (The URL to the logo of this song/station),
        @param station_id is the unique ID of the song / station to play.
        @return A dict with the tag url.
        """
        # <result><url>http://..../logo.jpg</url></result>
        resp = self.send_cmd('play_url', params=dict(id=station_id))
        return resp['result']

    def search_station(self, searchstr):
        """!
        Search for a station by (part of the) name.
        When the device is showing a menu of radio stations it is possible to search for a station
        name by specifying a search string. Any station matching that string will be presented in
        a search result menu. The unique ID of that result menu is returned, so it can be retrieved
        with the function get_menu().
        The proper sequence of actions to perform is:
          (1) search for the station, eg with 'slam' as search string: search_station('slam')
          (2) retrieve the menu-id from the result, eg {'id': 100} -> menu-ID is 100.
          (3) enter the menu, using enter_menu(100)
          (4) retrieve the results, using get_menu(menu_id=100, start=1, count=250)
        On return:
         - id (ID of the result list)
         - rt (containing the status text, eg 'OK').
        @param searchstr holds the part of the name to search for.
        @return A dict with the tags rt and id.
        """
        # <result><id>100</id><rt>OK</rt></result>
        resp = self.send_cmd('searchstn', params=dict(str=searchstr))
        return resp['result']

    def send_bt_command(self, cmdnr):
        """!
        Send a BlueTooth command.
        The device can send several BlueTooth commands. Each one of them is assigned a
        number. This function allows to send the given bluetooth command number to the
        radio device.
        Possible bluetooth commands are:
         - 1: ??
         - 3: ?? connect?
         - 4: ??
        On return:
         - rt (containing the status text, eg 'OK').
        @param cmdnr is the Bluetooth command numer to execute.
        @return A dict with the tag rt.
        """
        # <result><rt>OK</rt></result>
        resp = self.send_cmd('BTCMD', params=dict(cmd=cmdnr))
        return resp['result']

    def send_rc_key(self, keynr):
        """!
        Simulate a key pressed on the remote control.
        The device comes with an InfraRed Remote. This function can be used to simulate
        a key being pressed on that remote.
        On return:
         - rt (containing the status text, eg 'OK').
        @param keynr is the key on the IR remote control to simulate.
        @return A dict with the tag rt.
        """
        # <result><rt>OK</rt></result>
        resp = self.send_cmd('Sendkey', params=dict(key=keynr))
        return resp['result']

    def send_bootlogo(self, url):
        """!
        Set the image the device will show when it boots.
        The moment the device boots it shows an image / logo.
        This image can be updated by this function.
        The new image must be indicated by the URL. The size must be fixed to hhh x www.
        Example: http://192.168.2.116:8889/mylogo.jpg
        Note that the device will display the new image only at boot due to a power cycle.
        On return:
         - rt (containing the status text, eg 'OK').
        @param url is the URL of the image to download.
        @return A dict with the tag rt.
        """
        # <result><rt>OK</rt></result>
        resp = self.send_cmd('mylogo', params=dict(url=url))
        return resp['result']

    def set_favourite(self, song_id, pos):
        """!
        Put the given song/station (song_id) on the favourites list on position 'pos'.
        This function will put the song / station with a unique ID, the combination of
        the given id and the item, on the favourites list at the given position.
        For example, when playing a radio station (selected from the menu with ID=87
        and item 114) the user wants to put this radio station in the favourites list
        at position 2.
        After the command has completed, radio station 87_114 will be found on position 2
        in the hotkeylist.
        On return:
         - rt (containing the status text, eg 'OK').
        @param song_id is the menu ID of the song or station, eg 87_114.
        @param pos is the position/index in the favourites list to put it in.
        @return A dict with the tag rt.
        """
        # <result><rt>OK</rt></result>
        if '_' in song_id:
            menu = song_id.split('_')
            menu_id = menu[0]
            menu_item = menu[1]
        else:
            return dict(rt='ERR: format error in ID {}. Must follow x_x notation.'.format(song_id))
        resp = self.send_cmd('setfav', params=dict(menu_id=menu_id, item=menu_item, pos=pos))
        return resp['result']

    def start_BT_match(self):
        """!
        Start matching with another BlueTooth (BT) device.
        The radio device will start the bluetooth matching proces.
        On return:
         - The status text, eg 'OK'.
        @return A dict with the status value.
        """
        resp = self.send_cmd('StartBTMatch')
        return resp['result']

    def stop(self):
        """!
        Stop playing the current song/station.
        A song (file) or a station is stopped playing and the device will return to
        the menu.
        On return:
         - rt (The status text, eg 'OK').
        @return A dict with the tag rt.
        """
        resp = self.send_cmd('stop')
        return resp['result']

    def back_stop(self):
        """!
        Stop / start playing the current song/station.
        A song (file) or a station is stopped or started playing.
        When stopped, the device will return to the menu holding the song / station.
        On return:
         - id (The unique ID of the menu the song/station is listed)
        @return A dict with the tag id.
        """
        resp = self.send_cmd('back_stop')
        return resp['result']

    def back(self):
        """!
        Navigate backwards in the menu.
        Move one item back (upwards) in the menu.
        On return:
         - id (The unique ID of the active menu)
        @return A dict with the tag id.
        """
        resp = self.send_cmd('back')
        return resp['result']

    def update_software(self):
        """!
        Order a software update.
        If the tag SWUpdate received as result of the init() function indicates 'YES', there
        might be a software update available. This function starts a software update and returns
        the upgrade status.
         - PROCESSING : The upgrade is still in progress.
         - OK : The upgrade finished.
        @return The software upgrade status, eg PROCESSING.
        """
        resp = self.send_cmd('updatenewsw')
        return resp['result']


def make_xml(text):
    """!
    Convert malformed XML into proper XML.
    The XML standard requires special characters, like an ampersand, to be escaped.
    The Airmusic implementation of XML does not escape such characters.
    Therefore, this function will replace special characters in the given text with
    their escaped counterparts.
    @param text is the XML-alike text, potentially with non-escaped characters.
    @return the escaped text.
    """
    return "{}".format(text.replace('&', '&amp;'))
