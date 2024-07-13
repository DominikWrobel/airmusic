#
# For more details, please refer to github at
# https://github.com/DominikWrobel/airmusic
#

# Imports and dependencies
import asyncio
from datetime import time, timedelta
import time
from urllib.error import HTTPError, URLError
import urllib.parse
import urllib.request
import aiohttp
import voluptuous as vol
import logging
import time
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

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
VERSION = '0.9'

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
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=8)
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
        self._pwstate = False
        self._volume = 0
        self._muted = False
        self._selected_source = ''
        self._selected_media_content_id = ''
        self._selected_media_title = ''
        self._image_url = {}
        self._source_name = None
        self._source_names = {}
        self._sources = {}
        self._unique_id = f"{self._host}-{self._name}"
        self._request_semaphore = asyncio.Semaphore(1)

    # Run when added to HASS TO LOAD CHANNELS
    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        await self.load_sources()
      
    # Load favorite radio stations
    async def load_sources(self):
        """Initialize the Airmusic device loading the sources."""
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        soup = BeautifulSoup(list_xml, features="xml")
    
        src_names = [src_name.string for src_name in soup.find_all('name')]
        sources = [src_reference.string for src_reference in soup.find_all('id')]
    
        self._source_names = src_names
        self._sources = dict(zip(src_names, sources))

    async def get_sources_reference(self):
        """Import BeautifulSoup."""
        # Get first bouquet reference
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        soup = BeautifulSoup(list_xml, features = "xml")
        return soup.find('status').renderContents().decode('UTF8')

    # Asnc API requests
    async def request_call(self, url):
        """Call web API request with rate limiting."""
        uri = 'http://' + self._host + url
        _LOGGER.debug("Airmusic: [request_call] - Call request %s ", uri)
        async with self._request_semaphore:
            async with self._opener.get(uri, auth=aiohttp.BasicAuth('su3g4go6sk7', 'ji39454xu/^', encoding='utf-8')) as resp:
                text = await resp.read()
            await asyncio.sleep(1)  # 1 second delay between requests
            return text

    # Component Update
    @Throttle(MIN_TIME_BETWEEN_SCANS)
    async def async_update(self):
        """Update device status."""
        playinfo_xml = await self.request_call('/playinfo')
        soup = BeautifulSoup(playinfo_xml, features="xml")
    
        # Update power state
        pwstate = soup.result.renderContents().decode('UTF8')
        self._update_power_state(pwstate)
    
        # If powered on, update other information
        if self._pwstate in ['playing', 'idle', 'buffering', 'paused']:
            self._update_media_info(soup)
            await self._update_volume_info()

    async def _update_volume_info(self):
        """Update volume and mute status."""
        volume_xml = await self.request_call('/background_play_status')
        soup = BeautifulSoup(volume_xml, features="xml")
        vol = soup.vol.renderContents().decode('UTF8')
        mute = soup.mute.renderContents().decode('UTF8')

        self._volume = int(vol) / MAX_VOLUME if vol else None
        self._muted = (mute == '1') if mute else None

    def _update_power_state(self, pwstate):
        """Update power state based on playinfo response."""
        if pwstate.find('FAIL') >= 0:
            self._pwstate = 'true'
        elif pwstate.find('INVALID_CMD') >= 0:
            self._pwstate = 'idle'
        elif pwstate.find('sid>1') >= 0:
            self._pwstate = 'idle'
        elif pwstate.find('sid>6') >= 0:
            self._pwstate = 'playing'
        elif pwstate.find('sid>2') >= 0:
            self._pwstate = 'buffering'
        elif pwstate.find('sid>9') >= 0:
            self._pwstate = 'paused'
        else:
            self._pwstate = 'unknown'

    def _update_media_info(self, soup):
        """Update media information from playinfo response."""
        current_time = int(time.time())
        self._selected_source = soup.station_info.renderContents().decode('UTF8') if soup.station_info else str(current_time)
        eventid = soup.artist.renderContents().decode('UTF8') if soup.artist else None
        eventtitle = soup.song.renderContents().decode('UTF8') if soup.song else None

        if self._selected_source != str(current_time):
            self._selected_media_title = ' - '.join(filter(None, [self._selected_source, eventid, eventtitle])) or None
        else:
            self._selected_media_title = ' - '.join(filter(None, [eventid, eventtitle])) or None

        self._selected_media_content_id = eventid
    
        # Update image URL
        imagelogo = soup.result.renderContents().decode('UTF8')
        if imagelogo.find('<album_img>') >= 0:
            self._image_url = f'http://{self._host}:{self._port}/album.jpg'
        elif imagelogo.find('<logo_img>') >= 0:
            self._image_url = f'http://{self._host}:{self._port}/playlogo.jpg'
        else:
            self._image_url = None

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

# GET - Radio station logo
    @property
    def media_image_url(self):
        """Image of current playing media."""
        if self._image_url:
            current_time = int(time.time())
            return f"{self._image_url}&t={current_time}"
        return None
        
    @Throttle(MIN_TIME_BETWEEN_SCANS)    
    async def async_update_media_image_url(self):
        """Update the media image URL."""
        if self._pwstate == 'playing':
            playinfo_xml = await self.request_call('/playinfo')
            soup = BeautifulSoup(playinfo_xml, features="xml")
            imagelogo = soup.result.renderContents().decode('UTF8')
            current_time = int(time.time())

            if imagelogo.find('<album_img>') >= 0:
                self._image_url = f'http://{self._host}:{self._port}/album.jpg?t={current_time}'
            elif imagelogo.find('<logo_img>') >= 0:
                self._image_url = f'http://{self._host}:{self._port}/playlogo.jpg?t={current_time}'
            else:
                self._image_url = None

            _LOGGER.debug("Airmusic: [update_media_image_url] - Image URL updated: %s", self._image_url)
        else:
            self._image_url = None

    async def async_get_media_image(self):
        """Fetch the media image of the current playing media."""
        _LOGGER.debug("Airmusic: [async_get_media_image] - Called with image URL: %s", self._image_url)

        if self._image_url is None:
            _LOGGER.debug("Airmusic: [async_get_media_image] - No image URL set")
            return None, None

        url = self._image_url if isinstance(self._image_url, str) else self._image_url.get('url')
        if not url:
            _LOGGER.debug("Airmusic: [async_get_media_image] - No valid URL found")
            return None, None

        try:
            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("Airmusic: [async_get_media_image] - Attempting to fetch image from: %s", url)
                async with session.get(url, auth=aiohttp.BasicAuth('su3g4go6sk7', 'ji39454xu/^')) as response:
                    if response.status == 200:
                        content = await response.read()
                        _LOGGER.debug("Airmusic: [async_get_media_image] - Successfully fetched image")
                        return content, response.content_type
                    else:
                        _LOGGER.debug("Airmusic: [async_get_media_image] - Failed to fetch image: %s", response.status)
                        return None, None
        except aiohttp.ClientError as e:
            _LOGGER.debug("Airmusic: [async_get_media_image] - Unable to fetch image: %s", str(e))
            return None, None
        except asyncio.TimeoutError:
            _LOGGER.debug("Airmusic: [async_get_media_image] - Timeout while fetching image")
            return None, None

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

# GET - Unique ID
    @property
    def unique_id(self):
        """Return the unique ID of the device."""
        return self._unique_id

# SET - Change source - From dropbox menu
    async def async_select_source(self, source):
        """Select input source."""
        _LOGGER.debug("Airmusic: [async_select_source] - Change radio source")
        await self.request_call('/play_stn?id=' + self._sources[source])
        self._source_name = source

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
        await self.request_call('/Sendkey?key=31')

# SET - Previous station
    async def async_media_previous_track(self):
        """Change to previous channel."""
        await self.request_call('/Sendkey?key=32')

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
        await self.request_call('/play_stn?id=' + self._sources[source])
