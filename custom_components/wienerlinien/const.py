"""Constants"""
DOMAIN = "wienerlinien"
CONF_STOPS = "stops"
CONF_FIRST_NEXT = "firstnext"

BASE_URL = "http://www.wienerlinien.at/ogd_realtime/monitor?rbl={}"

DEPARTURES = {
    "first": {"key": 0, "name": "{} first departure"},
    "next": {"key": 1, "name": "{} next departure"},
}
