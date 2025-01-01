# Wiener Linien API Documentation

The integration uses the real-time monitor API endpoint: `http://www.wienerlinien.at/ogd_realtime/monitor?rbl={stopId}`

## Response Structure

The API returns JSON data with the following structure:

```json
{
  "data": {
    "monitors": [
      {
        "locationStop": {
          "properties": {
            "title": "Stop Name"
          }
        },
        "lines": [
          {
            "name": "Line number/name",
            "towards": "Final destination",
            "direction": "H or R",
            "platform": "Platform number/name",
            "departures": {
              "departure": [
                {
                  "departureTime": {
                    "timePlanned": "YYYY-MM-DDThh:mm:ssZ",
                    "timeReal": "YYYY-MM-DDThh:mm:ssZ",
                    "countdown": 5
                  }
                }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

## Field Descriptions

- `locationStop.properties.title`: The name of the stop
- `lines[].name`: The line number or name (e.g., "U1", "40A")
- `lines[].towards`: The final destination of this line
- `lines[].direction`: Direction indicator ("H" = outward, "R" = return)
- `lines[].platform`: The platform number or name where the vehicle arrives
- `departures.departure[]`: Array of upcoming departures
  - `departureTime.timePlanned`: Scheduled departure time
  - `departureTime.timeReal`: Actual departure time (if available)
  - `departureTime.countdown`: Minutes until departure

## Notes

- The `timeReal` field may not always be present if there's no real-time data available
- Times are in ISO 8601 format with timezone information
- The API returns data licensed under CC BY 3.0 AT from Stadt Wien – data.wien.gv.at

## Example Response

```json
{
  "data": {
    "monitors": [
      {
        "locationStop": {
          "properties": {
            "title": "Karlsplatz"
          }
        },
        "lines": [
          {
            "name": "U1",
            "towards": "Leopoldau",
            "direction": "H",
            "platform": "1",
            "departures": {
              "departure": [
                {
                  "departureTime": {
                    "timePlanned": "2023-05-20T14:05:00Z",
                    "timeReal": "2023-05-20T14:06:30Z",
                    "countdown": 3
                  }
                }
              ]
            }
          }
        ]
      }
    ]
  }
}
