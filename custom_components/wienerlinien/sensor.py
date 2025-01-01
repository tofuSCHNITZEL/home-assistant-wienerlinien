"""
A integration that allows you to get information about next departure from specified stop.
For more details about this component, please refer to the documentation at
https://github.com/tofuSCHNITZEL/home-assistant-wienerlinien

API Response Structure:
    {
        "data": {
            "monitors": [{
                "locationStop": {
                    "properties": {
                        "title": "Stop Name"
                    }
                },
                "lines": [{
                    "name": "Line number/name",
                    "towards": "Final destination",
                    "direction": "H or R", # H=outward, R=return
                    "platform": "Platform number",
                    "departures": {
                        "departure": [{
                            "departureTime": {
                                "timePlanned": "YYYY-MM-DDThh:mm:ssZ",
                                "timeReal": "YYYY-MM-DDThh:mm:ssZ",
                                "countdown": minutes
                            }
                        }]
                    }
                }]
            }]
        }
    }
"""
import logging
from datetime import timedelta

import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import Entity

from custom_components.wienerlinien.const import BASE_URL, DEPARTURES

CONF_STOPS = "stops"
CONF_APIKEY = "apikey"
CONF_FIRST_NEXT = "firstnext"
CONF_NAME = "name"  # Add name configuration

SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_APIKEY): cv.string,
        vol.Optional(CONF_STOPS, default=None): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_FIRST_NEXT, default="first"): cv.string,
        vol.Optional(CONF_NAME): cv.string,  # Add name to schema
    }
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup."""
    stops = config.get(CONF_STOPS)
    firstnext = config.get(CONF_FIRST_NEXT)
    custom_name = config.get(CONF_NAME)
    dev = []
    for stopid in stops:
        api = WienerlinienAPI(async_create_clientsession(hass), hass.loop, stopid)
        data = await api.get_json()
        try:
            name = data["data"]["monitors"][0]["locationStop"]["properties"]["title"]
        except Exception:
            raise PlatformNotReady()
        dev.append(WienerlinienSensor(api, name, firstnext, stopid, custom_name))
    add_devices_callback(dev, True)


class WienerlinienSensor(SensorEntity, BinarySensorEntity):
    """WienerlinienSensor."""

    def __init__(self, api, name, firstnext, stopid, custom_name=None):
        """Initialize."""
        self.api = api
        self.firstnext = firstnext
        self._name = custom_name or name
        self._state = None
        self.attributes = {}
        self._stop_id = stopid
        self._base_name = name  # Store original stop name

    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"wienerlinien_{self._stop_id}_{self.firstnext}"

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
            line = data["monitors"][0]["lines"][0]
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
                "countdown": departure["departureTime"]["countdown"],
            }
        except Exception:
            pass

    @property
    def name(self):
        """Return name."""
        line_name = self.attributes.get("name", "")
        if line_name:
            return f"{line_name}, {DEPARTURES[self.firstnext]['name'].format(self._name)}"
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
        """Return icon with different states based on countdown."""
        try:
            countdown = self.attributes.get("countdown")
            return "mdi:bus" if countdown is None or countdown > 1 else "mdi:bus-alert"
        except (TypeError, ValueError):
            return "mdi:bus"

    @property
    def extra_state_attributes(self):
        """Return attributes."""
        return self.attributes

    @property
    def device_class(self):
        """Return device_class."""
        return "timestamp"

    @property
    def is_on(self):
        """Return true if departure is imminent (<=1 minute)."""
        try:
            countdown = self.attributes.get("countdown")
            return countdown is not None and countdown <= 1
        except (TypeError, ValueError):
            return None

    @property 
    def binary_sensor_device_class(self):
        """Return binary sensor device class."""
        return "running"


class WienerlinienAPI:
    """Call Wiener Linien API.
    
    The API endpoint returns real-time departure information for a given stop ID.
    Base URL: http://www.wienerlinien.at/ogd_realtime/monitor?rbl={stopId}
    
    Data Fields:
        - locationStop.properties.title: Name of the stop
        - lines[].name: Line number/name (e.g. "U1", "40A")
        - lines[].towards: Final destination
        - lines[].direction: "H" (outward) or "R" (return)
        - lines[].platform: Platform number/name
        - departures.departure[]: List of upcoming departures
            - departureTime.timePlanned: Scheduled time
            - departureTime.timeReal: Actual time (if available)
            - departureTime.countdown: Minutes until departure

    Note: Times are in ISO 8601 format with timezone information
    License: CC BY 3.0 AT from Stadt Wien – data.wien.gv.at
    """

    def __init__(self, session, loop, stopid):
        """Initialize.
        
        Args:
            session: aiohttp client session
            loop: asyncio event loop
            stopid: RBL stop ID
        """
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
