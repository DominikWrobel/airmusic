"""
Support for Airmusic Internet Radios.
"""
#
# For more details, please refer to github at
# https://github.com/DominikWrobel/airmusic
#

# Imports and dependencies
import asyncio
from datetime import timedelta
from urllib.error import HTTPError, URLError
import urllib.parse
import urllib.request
import aiohttp
import voluptuous as vol
import requests
from requests.auth import HTTPBasicAuth

# From homeassitant

from custom_components.airmusic import _LOGGER, DOMAIN as AIRMUSIC_DOMAIN
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_ALBUM, 
    MEDIA_TYPE_ARTIST,
    MEDIA_TYPE_PLAYLIST,
    MEDIA_TYPE_CHANNEL
)

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType
)

from homeassistant.const import (
    STATE_OFF, 
    STATE_ON, 
    STATE_UNKNOWN,
    STATE_PLAYING, 
    STATE_PAUSED, 
    STATE_IDLE,
    STATE_BUFFERING,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PREVIOUS_TRACK
)

import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

# VERSION
VERSION = '0.3'

# Dependencies
from .airmusicapi import airmusic

# DEFAULTS
DEFAULT_PORT = 8080
DEFAULT_NAME = "Airmusic Radio"
DEFAULT_TIMEOUT = 50
DEFAULT_USERNAME = 'roosu3g4go6sk7'
DEFAULT_PASSWORD = 'ji39454xu/^'
DEFAULT_SOURCE = ''
DEFAULT_IMAGE = 'logo'

# Return cached results if last scan was less then this time ago.
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=5)

SUPPORT_AIRMUSIC = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
)

MAX_VOLUME = 30

# SETUP PLATFORM
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""                         
    """Initialize the Airmusic device."""
    devices = []
    airmusic_list = hass.data[AIRMUSIC_DOMAIN]

    for device in airmusic_list:
        _LOGGER.debug("Configured a new AirmusicMediaPlayer %s",
                      device.get_host)
        devices.append(AirmusicMediaPlayer(device))

    async_add_entities(devices, update_before_add=True)

# Airmusic Media Player Device
class AirmusicMediaPlayer(MediaPlayerEntity):
    """Representation of a Airmusic Media Player device."""

    def __init__(self, AirmusicMediaPlayerEntity):
        """Initialize the Airmusic device."""
        self._host = AirmusicMediaPlayerEntity.get_host
        self._port = AirmusicMediaPlayerEntity.get_port
        self._name = AirmusicMediaPlayerEntity.get_name
        self._username = AirmusicMediaPlayerEntity.get_username
        self._password = AirmusicMediaPlayerEntity.get_password
        self._timeout = AirmusicMediaPlayerEntity.get_timeout
        self._source = AirmusicMediaPlayerEntity.get_source
        self._image = AirmusicMediaPlayerEntity.get_image
        self._opener = AirmusicMediaPlayerEntity.get_opener
        self._pwstate = False #True
        self._volume = 0
        self._muted = False
        self._selected_source = ''
        self._selected_media_content_id = ''
        self._selected_media_title = ''
        self._image_url = None
        self._source_names = {}
        self._sources = {}

    # Run when added to HASS TO LOAD CHANNELS
    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        await self.load_sources()
      
    # Load channels from specified channels
    async def load_sources(self):
        """Initialize the Airmusic device loading the sources."""
        from bs4 import BeautifulSoup
        if self._source:
            # Load user set channels.
            _LOGGER.debug("Airmusic: [load_source] - Request user sources %s ",
                          self._source)
            list_xml = await self.request_call('/list?id=75&start=1&count=20')

            # Channel name
            soup = BeautifulSoup(list_xml, features = "xml")
            src_names = soup.find_all('name')
            self._source_names = [src_name.string for src_name in src_names]
            # Channel reference
            src_references = soup.find_all('id')
            sources = [src_reference.string for src_reference in
                       src_references]
            self._sources = dict(zip(self._source_names, sources))

        else:
            # Load channels from first bouquet.
            reference = urllib.parse.quote_plus(await self.get_sources_reference())
            _LOGGER.debug("Airmusic: [load_sources] - Request reference %s ",
                          reference)
            list_xml = await self.request_call('/list?id=75&start=1&count=20')

            # Channel name
            soup = BeautifulSoup(list_xml, features = "xml")
            src_names = soup.find_all('name')
            self._source_names = [src_name.string for src_name in src_names]

            # Channel reference
            src_references = soup.find_all('id')
            sources = [src_reference.string for src_reference in
                       src_references]
            self._sources = dict(zip(self._source_names, sources))

    async def get_sources_reference(self):
        """Import BeautifulSoup."""
        from bs4 import BeautifulSoup
        # Get first bouquet reference
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        soup = BeautifulSoup(list_xml, features = "xml")
        return soup.find('status').renderContents().decode('UTF8')

    # Asnc API requests
    async def request_call(self, url):
        """Call web API request."""
        uri = 'http://' + self._host + ":" + url
        _LOGGER.debug("Airmusic: [request_call] - Call request %s ", uri)
        # Check if is password enabled
        if self._password is not None:
            # Handle HTTP Auth
            async with self._opener.get(uri, auth=aiohttp.BasicAuth('su3g4go6sk7', 'ji39454xu/^', encoding='utf-8')) as resp:
                text = await resp.read()
                return text
        else:
            async with self._opener.get(uri, auth=aiohttp.BasicAuth('su3g4go6sk7', 'ji39454xu/^', encoding='utf-8')) as resp:
                text = await resp.read()
                return text

    # Component Update
    @Throttle(MIN_TIME_BETWEEN_SCANS)
    async def async_update(self):
        """Import BeautifulSoup."""
        from bs4 import BeautifulSoup
        # Get the latest details from the device.
        _LOGGER.debug("Airmusic: [update] - request for host %s (%s)", self._host,
                     self._name)
        playinfo_xml = await self.request_call('/playinfo')
        soup = BeautifulSoup(playinfo_xml, features = "xml")
        pwstate = soup.result.renderContents().decode('UTF8')
        self._pwstate = ''

        _LOGGER.debug("Airmusic: [update] - Powerstate for host %s = %s",
                      self._host, pwstate)
        if pwstate.find('FAIL') >= 0:
            self._pwstate = 'true'

        if pwstate.find('INVALID_CMD') >= 0:
            init_xml = await self.request_call('/init')
            self._pwstate = 'idle'

        if pwstate.find('sid>1') >= 0:
            self._pwstate = 'idle'

        if pwstate.find('sid>6') >= 0:
            self._pwstate = 'playing'

        if pwstate.find('sid>2') >= 0:
            self._pwstate = 'buffering'

        if pwstate.find('sid>9') >= 0:
            self._pwstate = 'paused'

        # If powered on
        if self._pwstate == 'playing':
            playinfo_xml = await self.request_call('/playinfo')
            soup = BeautifulSoup(playinfo_xml, features = "xml")
            servicename = soup.station_info.renderContents().decode('UTF8')
            reference = soup.sid.renderContents().decode('UTF8')
            eventtitle = soup.song.renderContents().decode('UTF8')
            eventid = soup.artist.renderContents().decode('UTF8')
#            response = await self.hass.async_add_executor_job(
#                requests.get,
#                'http://''su3g4go6sk7:ji39454xu%2F%5E@' + self._host + ':' + str(self._port) + '/playlogo.jpg'
#            )
#            self._image_url = response.url

            _LOGGER.debug("Airmusic: [update] - Eventtitle for host %s = %s",
                          self._host, eventtitle)
            # Info of selected source and title
            self._selected_source = servicename 
            self._selected_media_content_id = eventid
            self._selected_media_title = servicename + ' - ' + eventid + ' - ' + eventtitle

        # Check volume and if is muted and update self variables
        if self._pwstate in ['playing','idle','buffering','paused']:
            volume_xml = await self.request_call('/background_play_status')
            soup = BeautifulSoup(volume_xml, features = "xml")
            vol = soup.vol.renderContents().decode('UTF8')
            mute = soup.mute.renderContents().decode('UTF8')

            self._volume = int(vol) / MAX_VOLUME if vol else None
            self._muted = (mute == '1') if mute else None
            _LOGGER.debug("Airmusic: [update] - Volume for host %s = %s",
                          self._host, vol)
            _LOGGER.debug("Airmusic: [update] - Is host %s muted = %s",
                          self._host, mute)

        return True

# GET - Name
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

# GET - State
    @property
    def state(self):
        """Return the state of the device."""
        if self._pwstate == 'true':
            return STATE_OFF
        if self._pwstate == 'idle':
            return STATE_IDLE
        if self._pwstate == 'buffering':
            return STATE_BUFFERING
        if self._pwstate == 'paused':
            return STATE_PAUSED
        if self._pwstate == 'playing':
            return STATE_PLAYING
        if self._pwstate == "init":
            return self._init

        return STATE_UNKNOWN

# GET - Volume Level
    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

# GET - Muted
    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

# GET - Features
    @property
    def supported_features(self):
        """Flag of media commands that are supported."""
        return SUPPORT_AIRMUSIC

# GET - Content type
    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_ARTIST

# GET - Content id - Current Station name
    @property
    def media_content_id(self):
        """Service Ref of current playing media."""
        return self._selected_media_content_id

# GET - Media title - Current Station name
    @property
    def media_title(self):
        """Title of current playing media."""
        return self._selected_media_title

# GET - Content image
    @property
    def media_image_url(self):
        """Image of current playing media."""
        _LOGGER.debug("Airmusic: [media_image_url] - %s", self._image_url)
        return self._image_url

# GET - Current source
    @property
    def source(self):
        """Return the current input source."""
        return self._selected_source

# GET - Next station
    def media_next_track(self):
        """Change to next channel."""
        return self._media_next_track

# GET - Current source list
    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_names

# SET - Change source - From dropbox menu
    async def async_select_source(self, source):
        """Select input source."""
        _LOGGER.debug("Airmusic: [async_select_source] - Change radio source")
        await self.request_call('/play_stn?id=' + self._sources[source])

# SET - Volume up
    async def async_volume_up(self):
        """Set volume level up."""
        await self.request_call('/Sendkey?key=9')

# SET - Volume down
    async def async_volume_down(self):
        """Set volume level down."""
        await self.request_call('/Sendkey?key=10')

# SET - Volume level
    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        volset = str(round(volume * MAX_VOLUME))
        await self.request_call('/setvol?vol=' + volset)

# SET - Volume mute
    async def async_mute_volume(self, mute):
        """Mute or unmute media player."""
        await self.request_call('/Sendkey?key=8')
#        self.async_update()

# SET - Media Play/pause
    async def async_media_play_pause(self):
        """Play pause media player."""
        await self.request_call('/Sendkey?key=29')

# SET - Media Play
    async def async_media_play(self):
        """Send play command."""
        await self.request_call('/Sendkey?key=29')

# SET - Media Pause
    async def async_media_pause(self):
        """Send media pause command to media player."""
        await self.request_call('/Sendkey?key=29')

# SET - Turn on
    async def async_turn_on(self):
        """Turn the media player on."""
        await self.request_call('/Sendkey?key=7')
#        self.async_update()

# SET - Turn off
    async def async_turn_off(self):
        """Turn off media player."""
        await self.request_call('/Sendkey?key=7')
#        self.async_update()

# SET - Next station
    async def async_media_next_track(self):
        """Change to next channel."""
        await self.request_call('/Sendkey?key=2')

# SET - Previous station
    async def async_media_previous_track(self):
        """Change to previous channel."""
        await self.request_call('/Sendkey?key=3')

# SET - Change to source
    async def async_play_media(self, media_type, media_id, **kwargs):
        """Support changing a source."""
        if media_type != MEDIA_TYPE_CHANNEL:
            _LOGGER.error('Unsupported media type')
            return
        try:
            cv.positive_int(media_id)
        except vol.Invalid:
            _LOGGER.error('Media ID must be positive integer')
            return
        # Hack to map remote key press
        # 2   Key "0"
        # 3   Key "1"
        # 4   Key "2"
        # 5   Key "3"
        # 6   Key "4"
#        for digit in media_id:
#            if digit == '0':
#                channel_digit = '11'
#            else:
#                channel_digit = int(digit)+1
        await self.request_call('/play_stn?id=' + self._sources[source])





