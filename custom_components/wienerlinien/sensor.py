"""
A integration that allows you to get information about next departure from specified stop.
For more details about this component, please refer to the documentation at
https://github.com/tofuSCHNITZEL/home-assistant-wienerlinien
"""
import logging
from datetime import timedelta

import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import Entity

from custom_components.wienerlinien.const import BASE_URL, DEPARTURES

CONF_STOPS = "stops"
CONF_APIKEY = "apikey"
CONF_FIRST_NEXT = "firstnext"

SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_APIKEY): cv.string,
        vol.Optional(CONF_STOPS, default=None): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_FIRST_NEXT, default="first"): cv.string,
    }
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup."""
    stops = config.get(CONF_STOPS)
    firstnext = config.get(CONF_FIRST_NEXT)
    dev = []
    for fullstopid in stops:
        if '/' in fullstopid:
            parts = fullstopid.split('/')
            stopid = parts[0]
            linespec = parts[1]
            _LOGGER.debug("Identified Stop: "+stopid+", Line: "+linespec)
        else:
            stopid = fullstopid
            linespec = None
            _LOGGER.debug("Identified Stop: "+stopid)

        api = WienerlinienAPI(async_create_clientsession(hass), hass.loop, stopid)
        data = await api.get_json()
        try:
            stopname = data["data"]["monitors"][0]["locationStop"]["properties"]["title"]
        except Exception:
            raise PlatformNotReady()
        dev.append(WienerlinienSensor(api, stopname, firstnext, linespec))
    add_devices_callback(dev, True)


class WienerlinienSensor(Entity):
    """WienerlinienSensor."""

    def __init__(self, api, stopname, firstnext, linespec):
        """Initialize."""
        self.api = api
        self.firstnext = firstnext
        self.linespec = linespec
        self.stopname = stopname
        self._name = stopname
        self._state = None
        self.attributes = {}

    async def async_update(self):
        """Update data."""
        try:
            data = await self.api.get_json()
            _LOGGER.debug(data)
            if data is None:
                return
            data = data.get("data", {})
        except:
            _LOGGER.debug("Could not get new state")
            return

        if data is None:
            return
        try:

            if self.linespec == None:
                line = data["monitors"][0]["lines"][0]
            else:
                line = None
                for monitor in data["monitors"]:
                    for linePos in monitor["lines"]:
                        lineName = linePos["name"]
                        if lineName.lower() == self.linespec.lower():
                            line = linePos
                            self._name = self.stopname + " ("+line["name"]+", "+line["towards"]+")"
                            break
                if line == None:
                    _LOGGER.debug("Could not find the line: " + self.linespec)
                    line = data["monitors"][0]["lines"][0]

            #line = data["monitors"][0]["lines"][0]
            departure = line["departures"]["departure"][
                DEPARTURES[self.firstnext]["key"]
            ]
            if "timeReal" in departure["departureTime"]:
                self._state = departure["departureTime"]["timeReal"]
            elif "timePlanned" in departure["departureTime"]:
                self._state = departure["departureTime"]["timePlanned"]
            else:
                self._state = self._state

            self.attributes = {
                "destination": line["towards"],
                "platform": line["platform"],
                "direction": line["direction"],
                "name": line["name"],
                "towards": line["towards"],
                "countdown": departure["departureTime"]["countdown"],
            }
        except Exception:
            pass

    @property
    def name(self):
        """Return name."""
        return DEPARTURES[self.firstnext]["name"].format(self._name)

    @property
    def state(self):
        """Return state."""
        if self._state is None:
            return self._state
        else:
            return f"{self._state[:-2]}:{self._state[26:]}"

    @property
    def icon(self):
        """Return icon."""
        return "mdi:bus"

    @property
    def extra_state_attributes(self):
        """Return attributes."""
        return self.attributes

    @property
    def device_class(self):
        """Return device_class."""
        return "timestamp"


class WienerlinienAPI:
    """Call API."""

    def __init__(self, session, loop, stopid):
        """Initialize."""
        self.session = session
        self.loop = loop
        self.stopid = stopid

    async def get_json(self):
        """Get json from API endpoint."""
        value = None
        url = BASE_URL.format(self.stopid)
        try:
            async with async_timeout.timeout(10):
                response = await self.session.get(url)
                value = await response.json()
        except Exception:
            pass

        return value
