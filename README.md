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
    - 4429
    - stop: 4429
      line: 100
      firstnext: next
    - 3230
```

## Configuration variables

key | description
-- | --
**platform (Required)** | The platform name.
**stops (Required)** | List of stopids or a stop with extended settings (see above)
**lineid (Optional)** | ID of a Wiener Linien transport line - some stops have more than one line so its always good to add the lineid to get the correct data
**firstnext (Optional)** | `first` or `next` departure. Default: `first` (can be defined at a specific stop as well to "overrule" the global setting)

## Sample overview

![Sample overview](overview.png)

## Notes

You can find out the Stop ID thanks to [Matthias Bendel](https://github.com/mabe-at) [https://till.mabe.at/rbl/](https://till.mabe.at/rbl/)  
The Line ID you can get from the URL in your browser after selecting a Line on the site (https://till.mabe.at/rbl/?**line=301**) or in this csv:
[wienerlinien-ogd-linien.csv](https://www.wienerlinien.at/ogd_realtime/doku/ogd/wienerlinien-ogd-linien.csv)


This platform is using the [Wienerlinien API](http://www.wienerlinien.at) API to get the information.
'Datenquelle: Stadt Wien – data.wien.gv.at'
Lizenz (CC BY 3.0 AT)

