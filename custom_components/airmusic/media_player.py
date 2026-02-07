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
import xml.etree.ElementTree as ET
import os

_LOGGER = logging.getLogger(__name__)

# From homeassitant

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import media_source
from homeassistant.components.upnp.const import DOMAIN as UPNP_DOMAIN
from homeassistant.components.media_source import is_media_source_id

from custom_components.airmusic import _LOGGER, DOMAIN as AIRMUSIC_DOMAIN

from homeassistant.components.media_player.browse_media import (
    BrowseMedia,
    async_process_play_media_url,
)

from homeassistant.components.media_player import (
    MediaClass,
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
from .const import DOMAIN, CONF_HOST, CONF_NAME

# VERSION
VERSION = '1.7'

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
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.MEDIA_ENQUEUE
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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Airmusic media player from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Setting up Airmusic media player from config entry")

    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]

    airmusic = AirmusicMediaPlayer(hass, host, name)

    async_add_entities([airmusic], update_before_add=True)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This should also be awaited
    return True

# Airmusic Media Player Device
class AirmusicMediaPlayer(MediaPlayerEntity):
    """Representation of a Airmusic Media Player device."""

    def __init__(self, hass, host, name):
        """Initialize the Airmusic device."""
        super().__init__()
        self.hass = hass
        self._host = host
        self._name = name
        self._port = 8080
        self._username = None
        self._password = None
        self._timeout = None
        self._source = None
        self._image = None
        self._opener = aiohttp.ClientSession()  # Initialize _opener
        self._state = None
        self._pwstate = None
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
        self._sleep_timer_count = 0
        self._sleep_timer_end_time = None
        self._is_local_playback = False

    # Run when added to HASS TO LOAD CHANNELS
    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        await self.load_sources()
        
        # Initialize UPnP
        self.upnp_device = None
        self.upnp_service = None
        await self._setup_upnp()

    # Setup UPnP
    async def _setup_upnp(self):
        """Set up UPnP for the device."""
        upnp_component = self.hass.data.get(UPNP_DOMAIN)
        if upnp_component:
            devices = upnp_component.devices
            for device in devices:
                if device.name == self._name:  # Match UPnP device to this media player
                    self.upnp_device = device
                    self.upnp_service = device.av_transport
                    break
        
        if not self.upnp_device:
            _LOGGER.warning("No matching UPnP device found for %s", self._name)
      
    # Load favorite radio stations
    async def load_sources(self):
        """Initialize the Airmusic device loading the sources."""
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        soup = BeautifulSoup(list_xml, features="xml")
    
        src_names = [src_name.string for src_name in soup.find_all('name')]
        sources = [src_reference.string for src_reference in soup.find_all('id')]
    
        self._source_names = src_names
        self._sources = dict(zip(src_names, sources))
        self._is_local_playback = False

    async def get_sources_reference(self):
        """Import BeautifulSoup."""
        # Get first bouquet reference
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        soup = BeautifulSoup(list_xml, features = "xml")
        return soup.find('status').renderContents().decode('UTF8')

    async def request_call(self, url):
        """Call web API request with rate limiting."""
        uri = f'http://{self._host}{url}'
        _LOGGER.debug("Airmusic: [request_call] - Call request %s ", uri)
        async with self._request_semaphore:
            try:
                async with self._opener.get(uri, auth=aiohttp.BasicAuth('su3g4go6sk7', 'ji39454xu/^', encoding='utf-8')) as resp:
                    text = await resp.text()
                await asyncio.sleep(1)  # 1 second delay between requests
                return text
            except aiohttp.ClientConnectorError as e:
                _LOGGER.error("Connection error: %s", str(e))
                return None

    # Component Update
    @Throttle(MIN_TIME_BETWEEN_SCANS)
    async def async_update(self):
        """Update device status."""
        playinfo_xml = await self.request_call('/playinfo')
        if not playinfo_xml:
            _LOGGER.warning("Airmusic: No response from device")
            return
            
        soup = BeautifulSoup(playinfo_xml, features="xml")

        # Update power state
        if soup.result:
            pwstate = soup.result.renderContents().decode('UTF8')
            self._update_power_state(pwstate)
        else:
            _LOGGER.warning("Airmusic: No result element in response")
            return

        # If powered on, update other information from same response
        if self._pwstate in ['playing', 'idle', 'buffering', 'paused']:
            self._update_media_info(soup)
            self._update_volume_info(soup)

    def _update_volume_info(self, soup):
        """Update volume and mute status from parsed XML."""
        if soup.vol:
            vol = soup.vol.renderContents().decode('UTF8')
            self._volume = int(vol) / MAX_VOLUME if vol else None
        else:
            self._volume = None
            
        if soup.mute:
            mute = soup.mute.renderContents().decode('UTF8')
            self._muted = (mute == '1') if mute else None
        else:
            self._muted = None

    def _update_power_state(self, pwstate):
        """Update power state based on playinfo response.
        
        Status ID (sid) meanings:
        1=not playing, 2=buffering, 5=buffer 100%, 6=playing,
        7=ending, 9=paused, 12=reading file, 14=failed to connect
        """
        if pwstate.find('FAIL') >= 0:
            self._pwstate = 'true'
        elif pwstate.find('INVALID_CMD') >= 0:
            self._pwstate = 'idle'
        elif pwstate.find('sid>6') >= 0:
            self._pwstate = 'playing'
        elif pwstate.find('sid>2') >= 0 or pwstate.find('sid>5') >= 0:
            self._pwstate = 'buffering'
        elif pwstate.find('sid>9') >= 0:
            self._pwstate = 'paused'
        elif pwstate.find('sid>1') >= 0 or pwstate.find('sid>7') >= 0 or pwstate.find('sid>12') >= 0 or pwstate.find('sid>14') >= 0:
            self._pwstate = 'idle'
        else:
            self._pwstate = 'unknown'

    def _update_media_info(self, soup):
        """Update media information from playinfo response."""
        current_time = int(time.time())
        self._selected_source = soup.station_info.renderContents().decode('UTF8') if soup.station_info else str(current_time)
        eventid = soup.artist.renderContents().decode('UTF8') if soup.artist else None
        eventtitle = soup.song.renderContents().decode('UTF8') if soup.song else None

        # Calculate remaining sleep time
        sleep_timer_info = ""
        if self._sleep_timer_end_time:
            remaining_time = max(0, int(self._sleep_timer_end_time - time.time()))
            if remaining_time > 0:
                minutes, seconds = divmod(remaining_time, 60)
                sleep_timer_info = f" [Sleep: {minutes:02d}:{seconds:02d}]"
            else:
                self._reset_sleep_timer()
                asyncio.create_task(self.async_turn_off())

        if self._selected_source != str(current_time):
            self._selected_media_title = ' - '.join(filter(None, [self._selected_source, eventid, eventtitle])) + sleep_timer_info
        else:
            self._selected_media_title = ' - '.join(filter(None, [eventid, eventtitle])) + sleep_timer_info

        self._selected_media_content_id = eventid

        # Check if sleep timer has ended
        if self._sleep_timer_end_time and time.time() >= self._sleep_timer_end_time:
            self._sleep_timer_count = 0
            self._sleep_timer_end_time = None
    
        # Update image URL
        imagelogo = soup.result.renderContents().decode('UTF8')
        if imagelogo.find('<album_img>') >= 0:
            self._image_url = f'http://{self._host}:8080/album.jpg'
        elif imagelogo.find('<logo_img>') >= 0:
            self._image_url = f'http://{self._host}:8080/playlogo.jpg'
        else:
            self._image_url = None

    async def async_will_remove_from_hass(self):
        """Cleanup when entity is removed from Home Assistant."""
        await self._opener.close()

# Browse media
    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
#            content_filter=lambda item: item.media_content_type.startswith("audio/"),
        )

# Play media
    async def async_play_media(self, media_type, media_id, **kwargs):
        """Play a piece of media."""
        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            media_id = play_item.url
            media_type = MediaType.MUSIC

        # Process the media URL
        processed_media_id = async_process_play_media_url(self.hass, media_id)

        if media_type == MediaType.MUSIC:
            if self.upnp_service:
                # Use UPnP to play the media
                await self.upnp_service.set_av_transport_uri(processed_media_id)
                await self.upnp_service.play()
                self._is_local_playback = True
            else:
                # Fallback to previous method if UPnP is not available
                encoded_url = urllib.parse.quote(processed_media_id, safe='')
                local_play_url = f"/LocalPlay?url={encoded_url}"
                await self.request_call(local_play_url)
                self._is_local_playback = True
        elif media_type == MediaType.CHANNEL:
            # Existing logic for playing radio stations
            try:
                cv.positive_int(processed_media_id)
            except vol.Invalid:
                _LOGGER.error('Media ID must be positive integer')
                return
            await self.request_call('/play_stn?id=' + self._sources[processed_media_id])
            self._is_local_playback = False
        else:
            _LOGGER.error("Unsupported media type")

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
        return MediaType.ARTIST

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
        self._is_local_playback = False 

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

# SET - Media Play/pause
    async def async_media_play_pause(self):
        """Play pause media player."""
        await self.request_call('/Sendkey?key=29')

# SET - Media Play
    async def async_media_play(self):
        """Send play command."""
        if self._is_local_playback and self.upnp_service:
            await self.upnp_service.play()
        else:
            await self.request_call('/Sendkey?key=29')

# SET - Media Pause
    async def async_media_pause(self):
        """Send pause command."""
        if self._is_local_playback and self.upnp_service:
            await self.upnp_service.pause()
        else:
            await self.request_call('/Sendkey?key=29')

# SET - Media Stop
    async def async_media_stop(self):
        """Send stop command."""
        if self._is_local_playback and self.upnp_service:
            await self.upnp_service.stop()
        else:
            await self.request_call('/Sendkey?key=30')

# SET - Turn on
    async def async_turn_on(self):
        """Turn the media player on."""
        await self.request_call('/Sendkey?key=7')

# SET - Turn off
    async def async_turn_off(self):
        """Turn off media player."""
        await self.request_call('/Sendkey?key=7')
        self._reset_sleep_timer()

# SET - Reset sleep timer
    def _reset_sleep_timer(self):
        """Reset the sleep timer."""
        self._sleep_timer_count = 0
        self._sleep_timer_end_time = None
        _LOGGER.debug("Sleep timer reset")

# SET - Next station or next track
    async def async_media_next_track(self):
        """Change to next track or channel."""
        if self._is_local_playback:
            if self.upnp_service:
                try:
                    await self.upnp_service.next()
                except Exception as e:
                    _LOGGER.error("UPnP next track failed: %s. Falling back to default method.", str(e))
                    await self.request_call('/Sendkey?key=31')
            else:
                await self.request_call('/Sendkey?key=31')
        else:
            await self.request_call('/Sendkey?key=112')

# SET - Set sleep timer or next track
    async def async_media_previous_track(self):
        """Change to previous track or manage sleep timer."""
        if self._is_local_playback:
            if self.upnp_service:
                try:
                    await self.upnp_service.previous()
                except Exception as e:
                    _LOGGER.error("UPnP previous track failed: %s. Falling back to default method.", str(e))
                    await self.request_call('/Sendkey?key=32')
            else:
                await self.request_call('/Sendkey?key=32')
        else:
            await self.request_call('/Sendkey?key=12')
            
            self._sleep_timer_count += 1
            if self._sleep_timer_count > 12:  # Reset after 180 minutes (12 * 15)
                self._reset_sleep_timer()
            else:
                sleep_duration = self._sleep_timer_count * 15 * 60  # Convert to seconds
                self._sleep_timer_end_time = time.time() + sleep_duration
        
        await self.async_update()
