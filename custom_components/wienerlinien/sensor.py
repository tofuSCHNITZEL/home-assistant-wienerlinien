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
CONF_STOP = "stop"
CONF_APIKEY = "apikey"
CONF_FIRST_NEXT = "firstnext"
CONF_LINEID = "line"
CONF_FIRST = "first"
CONF_NEXT = "next"

SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_APIKEY): cv.string,
        vol.Required(CONF_STOPS): vol.All(
            cv.ensure_list, 
            [
                {
                    vol.Required(CONF_STOP): vol.Coerce(int),
                    vol.Optional(CONF_LINEID): vol.Coerce(int),
                    vol.Optional(CONF_FIRST_NEXT, default="first"): vol.In({CONF_FIRST,CONF_NEXT}),
                },
                vol.Coerce(int)            
            ]
        ),
        vol.Optional(CONF_FIRST_NEXT, default="first"): vol.In({CONF_FIRST,CONF_NEXT}),
    }
)


_LOGGER = logging.getLogger(__name__)

UNIQUE_MONITORS = set()

async def async_setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup."""
    stops = config.get(CONF_STOPS)
    globalfirstnext = config.get(CONF_FIRST_NEXT)
    dev = []
    monitorid = 0
    lineid = None
    
    for stop in stops:
        if type(stop) is int:       
            stopid = stop
            firstnext = globalfirstnext
        else:            
            stopid = stop[CONF_STOP]
            lineid = stop.get(CONF_LINEID)
            firstnext = stop[CONF_FIRST_NEXT]

        api = WienerlinienAPI(async_create_clientsession(hass), hass.loop, stopid)
        data = await api.get_json()
        try:
            monitors = data["data"]["monitors"]
        except Exception:
            raise PlatformNotReady()
        
        if len(monitors) == 0:
            _LOGGER.error(f"Invalid stopid provided - there are no monitors for stopid {stopid}")
            continue
        
        if lineid:
            for monitorCount, monitor in enumerate(monitors):
                if monitor["lines"][0].get("lineId") == lineid:
                    monitorid = monitorCount
        
        stopname = monitors[monitorid]["locationStop"]["properties"]["title"].strip()
        linename = monitors[monitorid]["lines"][0]["name"].strip()
        destination = monitors[monitorid]["lines"][0]["towards"].strip()
        vehicle_type = monitors[monitorid]["lines"][0]["type"]
        
        name = f"{stopname} {linename} -> {destination}"
        monitorID = name+firstnext
        
        if monitorID not in UNIQUE_MONITORS:
            UNIQUE_MONITORS.add(monitorID)
            dev.append(WienerlinienSensor(api, name, firstnext, monitorid, vehicle_type))
        else:
            _LOGGER.warn("Skipping already existing monitor")
        
    add_devices_callback(dev, True)

class WienerlinienSensor(Entity):
    """WienerlinienSensor."""

    def __init__(self, api, name, firstnext, monitorid, vehicle_type):
        """Initialize."""
        self.api = api
        self.firstnext = firstnext
        self.monitorid = monitorid
        self.vehicle_type = vehicle_type
        self._name = name
        self._state = None
        self.attributes = {}
        self._attr_unique_id = f"{name}-{firstnext}".replace(" ", "-")

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
            line = data["monitors"][self.monitorid]["lines"][0]
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
                "stopid": self.api.my_stopid(),
                "lineid": line["lineId"],
                "barrierFree": line["barrierFree"],
                "trafficjam": line["trafficjam"],
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
        """Return icon according to vehicle."""
        match self.vehicle_type:
            case "ptMetro":
                return "mdi:subway"
            case "ptTram":
                return "mdi:tram"
            case "ptTramWLB":
                return "mdi:train-variant"
            case "ptBusCity":
                return "mdi:bus"
            case "ptBusNight":
                return "mdi:bus-clock"
            case "ptTrainS":
                return "mdi:train"     
            case _:
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
    
    def my_stopid(self):
        return self.stopid
