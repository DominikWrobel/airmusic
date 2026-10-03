#
# For more details, please refer to github at
# https://github.com/DominikWrobel/airmusic
#

import asyncio
from datetime import timedelta
import hashlib
import html
import logging
import mimetypes
import os
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

import aiohttp
from bs4 import BeautifulSoup
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import media_source
from homeassistant.components.upnp.const import DOMAIN as UPNP_DOMAIN
from homeassistant.components.media_player.browse_media import BrowseMedia, async_process_play_media_url
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaType
from homeassistant.const import STATE_OFF, STATE_UNKNOWN, STATE_PLAYING, STATE_PAUSED, STATE_IDLE, STATE_BUFFERING
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

from .const import DOMAIN, CONF_HOST, CONF_NAME, DEFAULT_USERNAME, DEFAULT_PASSWORD
from .transport import RadioTransport
from .stations import CONF_STATIONS, DEFAULT_STATIONS, find_station

_LOGGER = logging.getLogger(__name__)

# VERSION
VERSION = '1.7'

# DEFAULTS
DEFAULT_PORT = 8080
DEFAULT_NAME = "Airmusic Radio"
DEFAULT_TIMEOUT = 50
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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Airmusic media player from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Setting up Airmusic media player from config entry")

    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]

    airmusic = AirmusicMediaPlayer(hass, host, name, entry.options.get(CONF_STATIONS, DEFAULT_STATIONS))
    hass.data[DOMAIN][entry.entry_id] = airmusic

    async_add_entities([airmusic], update_before_add=True)

    return True

# Airmusic Media Player Device
class AirmusicMediaPlayer(MediaPlayerEntity):
    """Representation of a Airmusic Media Player device."""

    def __init__(self, hass, host, name, stations=None):
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
        self._transport = RadioTransport(hass, host, aiohttp.BasicAuth(
            DEFAULT_USERNAME, DEFAULT_PASSWORD, encoding='utf-8'))
        self._state = None
        self._pwstate = None
        self._volume = None
        self._muted = None
        self._selected_source = ''
        self._selected_media_content_id = ''
        self._selected_media_title = ''
        self._artwork_title = ''
        self._image_url = None
        self._fallback_image_path = None
        self._fallback_image_content_type = None
        self._fallback_image_hash = None
        self._source_name = None
        self._source_names = {}
        self._sources = {}
        self._unique_id = f"{self._host}-{self._name}"
        self._sleep_timer_count = 0
        self._sleep_timer_end_time = None
        self._is_local_playback = False
        self._stations = [dict(s) for s in (DEFAULT_STATIONS if stations is None else stations)]
        self._init_station_name = None
        self._last_track_uri = None
        self._attr_available = True
        self._update_lock = asyncio.Lock()
        self._image_cache = None
        self._image_cache_key = None
        self._image_cache_time = 0
        self._last_init_time = 0
        self._last_sources_time = 0
        self.upnp_device = None
        self.upnp_service = None

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
            devices = getattr(upnp_component, 'devices', ())
            if isinstance(upnp_component, dict):
                devices = upnp_component.get('devices', ())
            if isinstance(devices, dict):
                devices = devices.values()
            for device in devices:
                if getattr(device, 'name', None) == self._name:  # Match UPnP device to this media player
                    self.upnp_device = device
                    self.upnp_service = getattr(device, 'av_transport', None)
                    break
        
        if not self.upnp_device:
            _LOGGER.warning("No matching UPnP device found for %s", self._name)
      
    # Load favorite radio stations
    async def load_sources(self):
        """Initialize the Airmusic device loading the sources."""
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        if not list_xml:
            return
        soup = BeautifulSoup(list_xml, features="xml")
    
        src_names = [src_name.string for src_name in soup.find_all('name')]
        sources = [src_reference.string for src_reference in soup.find_all('id')]
    
        self._source_names = src_names
        self._sources = dict(zip(src_names, sources))
        self._last_sources_time = time.monotonic()

    async def get_sources_reference(self):
        """Import BeautifulSoup."""
        # Get first bouquet reference
        list_xml = await self.request_call('/list?id=75&start=1&count=20')
        if not list_xml:
            return None
        soup = BeautifulSoup(list_xml, features="xml")
        status = soup.find('status')
        return status.get_text() if status else None

    async def request_call(self, url):
        """Call the API using the shared one-second radio gate."""
        return await self._transport.request("GET", f"http://{self._host}{url}")

    async def get_track_uri(self):
        """Get the current stream URL from AVTransport GetPositionInfo."""
        url = f"http://{self._host}:52525/AVTransport/Control"

        body = """<?xml version=\"1.0\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\"
 s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
 <s:Body>
  <u:GetPositionInfo xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
   <InstanceID>0</InstanceID>
  </u:GetPositionInfo>
 </s:Body>
</s:Envelope>"""

        headers = {
            "Content-Type": 'text/xml; charset="utf-8"',
            "SOAPACTION": '"urn:schemas-upnp-org:service:AVTransport:1#GetPositionInfo"',
        }

        try:
            text = await self._transport.request(
                "POST", url, data=body, headers=headers, authenticate=False)
            if not text:
                return None

            # Normal XML response: <TrackURI>http://...</TrackURI>
            match = re.search(
                r"<TrackURI>(.*?)</TrackURI>",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if match:
                track_uri = html.unescape(match.group(1).strip())
                _LOGGER.debug("Airmusic: current TrackURI: %s", track_uri)
                return track_uri

            _LOGGER.debug("Airmusic: TrackURI not found in AVTransport response")

        except Exception as err:
            _LOGGER.debug("Airmusic: unable to get TrackURI: %s", err)

        return None

    def _station_name_from_track_uri(self, track_uri):
        station = find_station(self._stations, track_uri)
        return station["name"] if station else None

    def update_station_options(self, stations):
        """Apply options without reloading the entity or losing its sleep timer."""
        self._stations = [dict(s) for s in stations]
        self._clear_image()
        self._last_track_uri = None

    def _clear_image(self):
        self._image_url = None
        self._fallback_image_path = None
        self._fallback_image_content_type = None
        self._fallback_image_hash = None

    def _set_configured_logo(self, logo):
        if not logo:
            return False
        if logo.startswith("/local/"):
            root = os.path.realpath(self.hass.config.path("www"))
            relative = unquote(urlsplit(logo).path[len("/local/"):])
            path = os.path.realpath(os.path.join(root, relative))
            if os.path.commonpath([root, path]) != root or not os.path.isfile(path):
                return False
            self._fallback_image_path = path
            self._fallback_image_content_type = mimetypes.guess_type(path)[0] or "image/png"
            self._fallback_image_hash = f"local-{path}-{os.stat(path).st_mtime_ns}"
        else:
            self._image_url = logo
        return True

    def _logo_filename_from_station_name(self, station_name):
        """Return logo file name in /config/www based on station name."""
        if not station_name:
            return None

        normalized = unicodedata.normalize("NFKD", station_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        safe_name = re.sub(r"[^a-z0-9]+", "", ascii_name.lower())

        if not safe_name:
            return None

        return f"{safe_name}.png"

    def _set_fallback_station_logo(self, station_name):
        """Use local /config/www logo if it exists; otherwise use no image."""
        self._fallback_image_path = None
        self._fallback_image_content_type = None
        self._fallback_image_hash = None

        logo_filename = self._logo_filename_from_station_name(station_name)
        if not logo_filename:
            return

        logo_path = self.hass.config.path("www", logo_filename)
        if not os.path.isfile(logo_path):
            _LOGGER.debug(
                "Airmusic: fallback logo not found for %s: %s",
                station_name,
                logo_path,
            )
            return

        self._fallback_image_path = logo_path
        self._fallback_image_content_type = (
            mimetypes.guess_type(logo_path)[0] or "image/png"
        )
        self._fallback_image_hash = f"local-{logo_filename}-{int(os.path.getmtime(logo_path))}"
        _LOGGER.debug(
            "Airmusic: using fallback logo for %s: %s",
            station_name,
            logo_path,
        )

    # Component Update
    @Throttle(MIN_TIME_BETWEEN_SCANS)
    async def async_update(self):
        """Update normal and background modes with common timer handling."""
        async with self._update_lock:
            try:
                await self._async_refresh()
            finally:
                await self._check_sleep_timer()

    @staticmethod
    def _parse_response(xml):
        if not xml:
            return None
        try:
            ET.fromstring(xml)
        except ET.ParseError:
            # Some firmware emits bare '&' in metadata or URL attributes.
            # Keep existing XML entities, CDATA, comments and processing
            # instructions intact; do not conceal other structural errors.
            xml = re.sub(
                r'<!\[CDATA\[.*?\]\]>|<!--.*?-->|<\?.*?\?>|'
                r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)',
                lambda match: '&amp;' if match.group(0) == '&' else match.group(0),
                xml,
                flags=re.DOTALL,
            )
            try:
                ET.fromstring(xml)
            except ET.ParseError:
                return None
        return BeautifulSoup(xml, features="xml")

    async def _async_refresh(self):
        xml = await self.request_call('/playinfo')
        soup = self._parse_response(xml)
        if soup is None:
            self._attr_available = False
            return
        # INVALID_CMD does not prove a lost session: affected firmware
        # reports it while audio is playing. Prefer the read-only endpoint.
        if soup is None or soup.find('sid') is None:
            await self._update_from_background()
            return
        self._attr_available = True
        self._update_power_state(xml)
        if self._pwstate in ['playing', 'idle', 'buffering', 'paused']:
            await self._update_media_info(soup)
            self._update_volume_info(soup)
        else:
            self._clear_media()
        await self._retry_sources()

    async def _retry_sources(self):
        if not self._sources and time.monotonic() - self._last_sources_time >= 60:
            self._last_sources_time = time.monotonic()
            await self.load_sources()

    async def _radio_init(self):
        """Restore API session and read the current station name."""
        self._init_station_name = None
        self._last_init_time = time.monotonic()
        xml = await self.request_call('/init?language=en')
        soup = self._parse_response(xml)
        if soup is None:
            return False
        tag = soup.find('cur_play_name')
        if tag:
            self._init_station_name = tag.get_text().strip() or None
        return 'INVALID_CMD' not in xml and 'FAIL' not in xml

    async def _update_from_background(self):
        xml = await self.request_call('/background_play_status')
        # Never initialize automatically from polling. /init can disturb
        # playback on some firmware; failure here means unavailable.
        soup = self._parse_response(xml)
        if soup is None or soup.find('sid') is None:
            self._attr_available = False
            return
        self._attr_available = True
        self._update_power_state(xml)
        # On affected firmware sid=1 also represents standby. There is no
        # independent power bit in this endpoint; preserve PR #8's convention.
        if soup.sid.get_text().strip() == '1':
            self._pwstate = 'true'
        self._update_volume_info(soup)
        if self._pwstate in ['playing', 'buffering', 'paused']:
            await self._update_media_info(soup)
        else:
            self._clear_media()
        await self._retry_sources()

    def _clear_media(self):
        self._selected_source = ''
        self._selected_media_title = ''
        self._artwork_title = ''
        self._selected_media_content_id = ''
        self._last_track_uri = None
        self._init_station_name = None
        self._clear_image()

    async def _check_sleep_timer(self):
        if self._sleep_timer_end_time and time.time() >= self._sleep_timer_end_time:
            # Do not toggle a confirmed off device back on. When unreachable,
            # keep the deadline and try again once state is available.
            if self._attr_available:
                if self._pwstate == 'true':
                    self._reset_sleep_timer()
                else:
                    await self.async_turn_off()

    def _update_volume_info(self, soup):
        if soup.vol:
            try:
                self._volume = max(0.0, min(1.0, int(soup.vol.get_text()) / MAX_VOLUME))
            except (ValueError, TypeError):
                _LOGGER.debug("AirMusic returned invalid volume")
        if soup.mute:
            mute = soup.mute.get_text().strip()
            if mute in ('0', '1'):
                self._muted = mute == '1'

    def _update_power_state(self, xml):
        """Parse sid as a whole value (sid=12 is not sid=1)."""
        if 'FAIL' in xml:
            self._pwstate = 'true'
            return
        soup = self._parse_response(xml)
        sid = soup.find('sid').get_text().strip() if soup and soup.find('sid') else None
        self._pwstate = {
            '1': 'idle', '2': 'buffering', '5': 'buffering', '6': 'playing',
            '7': 'idle', '9': 'paused', '12': 'idle', '14': 'idle',
        }.get(sid, 'unknown')

    async def _update_media_info(self, soup):
        """Resolve station metadata and reset artwork on every station change."""
        def value(tag):
            element = soup.find(tag)
            return element.get_text().strip() if element else ''

        reported_name = value('station_info')
        # Always inspect TrackURI: custom names/logos may override radio data.
        track_uri = await self.get_track_uri()
        changed = track_uri != self._last_track_uri
        if changed:
            self._init_station_name = None
        self._last_track_uri = track_uri
        rule = find_station(self._stations, track_uri, reported_name)
        # Names must come from this read-only response or user mappings.
        # Do not call /init just to discover a name during playback.
        station = rule['name'] if rule else reported_name
        self._selected_source = station or ''
        artist, song = value('artist'), value('song')
        suffix = ''
        if self._sleep_timer_end_time:
            seconds = max(0, int(self._sleep_timer_end_time - time.time()))
            if seconds:
                minutes, seconds = divmod(seconds, 60)
                suffix = f" [Sleep: {minutes:02d}:{seconds:02d}]"
        self._artwork_title = ' - '.join(filter(None, [station, artist, song]))
        self._selected_media_title = self._artwork_title + suffix
        self._selected_media_content_id = artist
        self._clear_image()
        # Explicit UI logo overrides radio artwork; otherwise retain existing
        # album -> station logo -> local file behavior.
        if rule and self._set_configured_logo(rule.get('logo', '')):
            return
        if soup.find('album_img') is not None:
            self._image_url = f'http://{self._host}:8080/album.jpg'
        elif soup.find('logo_img') is not None:
            self._image_url = f'http://{self._host}:8080/playlogo.jpg'
        elif station:
            self._set_fallback_station_logo(station)

    async def async_will_remove_from_hass(self):
        """Cleanup when entity is removed from Home Assistant."""
        await self._transport.close()
        await super().async_will_remove_from_hass()

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
                await self._transport.serialized(lambda: self.upnp_service.set_av_transport_uri(processed_media_id))
                await self._transport.serialized(lambda: self.upnp_service.play())
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
        """Image address; HA serves authenticated radio artwork via its proxy."""
        return self._image_url

    @property
    def media_image_hash(self):
        if self._fallback_image_hash:
            return self._fallback_image_hash
        if self._image_url:
            # Periodically invalidate constant radio album.jpg URLs as well.
            key = f"{self._image_url}|{self._artwork_title}|{int(time.time()) // 30}"
            return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
        return None

    async def async_update_media_image_url(self):
        """Metadata updates already resolve artwork without a duplicate poll."""
        return None

    async def async_get_media_image(self):
        if self._fallback_image_path:
            path = self._fallback_image_path
            content_type = self._fallback_image_content_type
            def read_image():
                try:
                    return Path(path).read_bytes(), content_type or 'image/png'
                except OSError:
                    return None, None
            return await self.hass.async_add_executor_job(read_image)
        url = self._image_url
        if not url:
            return None, None
        key = (url, self._artwork_title)
        if self._image_cache_key == key and time.monotonic() - self._image_cache_time < 30:
            return self._image_cache
        is_radio = urlsplit(url).hostname == self._host.lower()
        if is_radio:
            result = await self._transport.request('GET', url, binary=True)
        else:
            # Never send radio credentials to a configured external logo URL.
            from homeassistant.helpers.aiohttp_client import async_get_clientsession
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    result = (await response.read(), response.content_type)
            except (aiohttp.ClientError, asyncio.TimeoutError):
                result = None
        if result:
            self._image_cache = result
            self._image_cache_key = key
            self._image_cache_time = time.monotonic()
        return result or (None, None)

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
        response = await self.request_call('/setvol?vol=' + volset)
        if response is not None and 'FAIL' not in response and 'INVALID_CMD' not in response:
            self._volume = max(0.0, min(1.0, round(volume * MAX_VOLUME) / MAX_VOLUME))

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
            await self._transport.serialized(lambda: self.upnp_service.play())
        else:
            await self.request_call('/Sendkey?key=29')

# SET - Media Pause
    async def async_media_pause(self):
        """Send pause command."""
        if self._is_local_playback and self.upnp_service:
            await self._transport.serialized(lambda: self.upnp_service.pause())
        else:
            await self.request_call('/Sendkey?key=29')

# SET - Media Stop
    async def async_media_stop(self):
        """Send stop command."""
        if self._is_local_playback and self.upnp_service:
            await self._transport.serialized(lambda: self.upnp_service.stop())
        else:
            await self.request_call('/Sendkey?key=30')

# SET - Turn on
    async def async_turn_on(self):
        """Turn the media player on."""
        await self.request_call('/Sendkey?key=7')

# SET - Turn off
    async def async_turn_off(self):
        """Turn off media player."""
        response = await self.request_call('/Sendkey?key=7')
        if response is not None and 'FAIL' not in response and 'INVALID_CMD' not in response:
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
                    await self._transport.serialized(lambda: self.upnp_service.next())
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
                    await self._transport.serialized(lambda: self.upnp_service.previous())
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
