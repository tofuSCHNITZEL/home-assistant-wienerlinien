[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Get information about next departures

A sensor platform which allows you to get information about departures from a specified Wiener Linien stop.

To get started install this with [HACS](https://hacs.xyz/)

## Example configuration.yaml

```yaml
sensor:
  platform: wienerlinien
  firstnext: first
  stops:
    - '4429'
    - '3230'
```

## Configuration variables

key | description
-- | --
**platform (Required)** | The platform name.
**stops (Required)** | RBL stop ID's
**firstnext (Optional)** | `first` or `next` departure.

## Sample overview

![Sample overview](overview.png)

## Notes

You can find out the Stop ID (rbl number) thanks to [Matthias Bendel](https://github.com/mabe-at) [https://till.mabe.at/rbl/](https://till.mabe.at/rbl/)

For detailed information about the API response structure, see the [API Documentation](docs/api.md).

This platform is using the [Wienerlinien API](http://www.wienerlinien.at) API to get the information.
'Datenquelle: Stadt Wien – data.wien.gv.at'
Lizenz (CC BY 3.0 AT)

