"""Station options, migration defaults and deterministic matching."""
from urllib.parse import urlsplit, unquote

CONF_STATIONS = "stations"

# Seed old installations once; runtime mappings are editable in HA options.
DEFAULT_STATIONS = [
    {"pattern": "r.dcs.redcdn.pl/sc/o2/Eurozet/live/antyradio.livx?audio=5", "name": "Antyradio", "logo": ""},
    {"pattern": "stream.rcs.revma.com/1nnezw8qz7zuv", "name": "Eska Rock", "logo": ""},
    {"pattern": "radiostream.pl/tuba8-1.mp3", "name": "Rock Radio", "logo": ""},
    {"pattern": "waw.ic.smcdn.pl/5380-1.mp3", "name": "Eska Rock Wa-wa", "logo": ""},
    {"pattern": "stream.rcs.revma.com/ypqt40u0x1zuv", "name": "Radio Nowy Świat", "logo": ""},
    {"pattern": "radiostream.pl/tuba8918-1.mp", "name": "Złote Przeboje", "logo": ""},
    {"pattern": "ml.cdn.eurozet.pl/mel-ldz.mp3", "name": "Meloradio", "logo": ""},
    {"pattern": "radiostream.pl/tuba10-1.mp3", "name": "TOK FM", "logo": ""},
    {"pattern": "stream.rcs.revma.com/an1ugyygzk8uv", "name": "Radio 357", "logo": ""},
]


def find_station(stations, track_uri, station_name=""):
    """Prefer the longest URI match; allow exact names for logo-only rules."""
    uri = (track_uri or "").casefold()
    matches = [s for s in stations if s.get("pattern") and
               s["pattern"].casefold() in uri]
    if matches:
        return max(matches, key=lambda s: len(s["pattern"]))
    name = station_name.strip().casefold()
    return next((s for s in stations if not s.get("pattern") and name and
                 s.get("name", "").casefold() == name), None)


def validate_station(value, stations, exclude=None):
    result = {k: str(value.get(k, "")).strip() for k in ("pattern", "name", "logo")}
    if not result["name"]:
        raise ValueError("name_required")
    if any(i != exclude and s.get("pattern", "").casefold() == result["pattern"].casefold()
           and (result["pattern"] or s.get("name", "").casefold() == result["name"].casefold())
           for i, s in enumerate(stations)):
        raise ValueError("duplicate_station")
    logo = result["logo"]
    parsed = urlsplit(logo)
    if logo and not (logo.startswith("/local/") or
                     parsed.scheme in ("http", "https") and parsed.hostname and
                     not parsed.username and not parsed.password):
        raise ValueError("invalid_logo")
    if logo.startswith("/local/") and any(part in ("..", ".") for part in
                                           unquote(parsed.path).split("/")):
        raise ValueError("invalid_logo")
    return result
