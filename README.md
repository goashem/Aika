# Aika: Time Information Script

This script provides comprehensive time and date information in Finnish or English, including astronomical data, weather
information, and environmental data.

## Features

### Time & Date

- Time expressed in natural language (e.g. "nearly ten to two")
- Precise time-of-day terms (early morning, morning, forenoon, noon, afternoon, early evening, late evening, night)
- Date information with proper grammar
- Percentage of year completed (including time of day)
- Seasonal information with automatic hemisphere detection
- Next holiday calculation with automatic country detection

### Astronomy

- Solar information (dawn, sunrise, noon, sunset, dusk, elevation, azimuth)
- Lunar information (phase percentage, growth status, elevation, azimuth, rise/set times)
- Next solar eclipse visible from your location (offline calculation)
- Next lunar eclipse visible from your location (offline calculation)
- Solar radiation data for solar panel owners

### Weather

- Weather information (temperature, humidity, pressure, wind)
    - Uses FMI as the primary source with Open-Meteo fallback
- Environmental data (air quality index, UV index)
- Marine data (wave height, direction, period)
- Sea water temperature and ice cover (Open-Meteo)
- Flood data (river discharge)
- Morning weather forecast (8 AM next day) with sunrise time

### Warnings

- Cold warnings (extreme, severe, moderate)
- Wind warnings (high wind, advisory)
- Precipitation warnings
- UV warnings
- Air quality warnings
- Road weather warnings (Finland only)
- Electricity price warnings (Finland only)
- Flood and wave warnings

### Finland-Specific Features

- **Road weather (Ajokeli)**
    - Driving conditions from Fintraffic Digitraffic API
- **Electricity price**
    - Current spot price from ENTSO-E (primary) with Porssisahko.net fallback (c/kWh)
    - CO₂ intensity of electricity generation (gCO₂/kWh) calculated from generation mix
    - Shows exact 15-minute timeslots for cheapest and most expensive future periods
    - Displays date indicators for tomorrow/later dates
- **Aurora forecast**
    - Kp-index from NOAA SWPC and FMI
- **Public transport disruptions** with automatic city detection (geofencing):
    - Turku area (Föli):
        - Alerts from Föli API
        - **Real-time traffic analysis**: Estimates local traffic conditions ("Normal", "Congested") by monitoring lateness of nearby buses
        - Nearest bus stops and next departures (Open Data, no API key needed)
    - Other cities: Digitransit with city-specific feed filtering (requires free API key)
    - Only shows alerts published within the last 24 hours

Supported cities for transit alerts:

| City      | Feed    | City         | Feed         |
|-----------|---------|--------------|--------------|
| Helsinki  | HSL     | Lappeenranta | Lappeenranta |
| Turku     | FOLI    | Rovaniemi    | Rovaniemi    |
| Tampere   | tampere | Kajaani      | Kajaani      |
| Oulu      | OULU    | Mikkeli      | Mikkeli      |
| Jyväskylä | LINKKI  | Raasepori    | Raasepori    |
| Kuopio    | Kuopio  | Salo         | Salo         |
| Lahti     | Lahti   | Hämeenlinna  | Hameenlinna  |
| Joensuu   | Joensuu | Kotka        | Kotka        |
| Vaasa     | Vaasa   | Kouvola      | Kouvola      |
| Pori      | Pori    |              |              |

### Other

- Configurable language (Finnish or English)
- Support for location-based timezones
- Automatic location detection from city names

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

Or use the virtual environment:

1. Create a `.venv` directory and install the dependencies there.
2. Run the script using the wrapper script

## Usage

### Using the wrapper script:

```bash
./aika.sh
```

### Direct Python execution:

```bash
python -m aika
```

### With location parameter:

```bash
./aika.sh "Helsinki"
python -m aika "New York"
```

## Library Usage

Aika can be used as a Python library to get structured data for your own applications.

### Get a Snapshot

The main entry point is `get_snapshot()`, which returns an `AikaSnapshot` object containing all raw and computed data.

```python
from aika import get_snapshot

# Get snapshot for coordinates (Helsinki)
snapshot = get_snapshot(latitude=60.1699, longitude=24.9384, language="fi")

# Access data
print(f"Location: {snapshot.location.city_name}")
print(f"Temperature: {snapshot.raw.weather.temperature}°C")
print(f"Time expression: {snapshot.computed.time_expression}")

# List all active warnings
for warning in snapshot.warnings:
    print(f"Warning: {warning}")
```

### Typed Models

All data is returned as typed dataclasses. You can import these for type hinting and building robust integrations:

```python
from aika import (
    AikaSnapshot, WeatherData, Location, RawData, ComputedData,
    DateInfo, SolarInfo, LunarInfo
)
```

## Package Structure

```
aika/
├── __init__.py          # Package exports (public API)
├── __main__.py          # CLI entry
├── api.py               # Public facade (get_snapshot)
├── models.py            # Typed dataclasses
├── providers/           # Raw data fetchers (FMI, Open-Meteo, etc.)
├── calculations/        # Pure data transformations
├── services/            # Domain orchestration
├── formats/             # Display and localization
├── core.py              # CLI orchestrator
├── config.py            # Configuration management
└── cache.py             # Caching logic
```

## Configuration

Location and language settings can be adjusted in `config.ini`:

- `latitude`: Geographic latitude
- `longitude`: Geographic longitude
- `timezone`: Timezone identifier
- `language`: Language preference (fi or en)

### API Keys

Some features require API keys. Add them to `config.ini`:

```ini
[api_keys]
digitransit = your-api-key-here
```

- **Digitransit** (public transport disruptions outside Turku): Register
  at [digitransit.fi](https://digitransit.fi/en/developers/api-registration/) to get a free API key.

Note: Turku area uses the Foli API which does not require an API key.

### Warning Thresholds

Default warning thresholds (can be modified in the code):

| Warning                      | Threshold   |
|------------------------------|-------------|
| Cold (moderate)              | <= -10C     |
| Cold (severe)                | <= -20C     |
| Cold (extreme)               | <= -30C     |
| Wind (advisory)              | >= 15 m/s   |
| Wind (high)                  | >= 25 m/s   |
| Electricity (expensive)      | >= 12 c/kWh |
| Electricity (very expensive) | >= 18 c/kWh |

## Data Sources

| Data              | Source                      | Requires Key |
|-------------------|-----------------------------|--------------|
| Weather           | FMI Open Data / Open-Meteo  | No           |
| Air Quality       | Open-Meteo                  | No           |
| Road Weather      | Fintraffic Digitraffic      | No           |
| Electricity Price | ENTSO-E (primary) / Porssisahko.net (fallback) | Yes (ENTSO-E API key) |
| Aurora (Kp)       | NOAA SWPC / FMI             | No           |
| Eclipses          | Calculated with ephem       | No (offline) |
| Transport (Turku) | Föli Open Data (GTFS/SIRI)  | No           |
| Transport (HSL)   | Digitransit HSL router      | Yes (free)   |
| Transport (other) | Digitransit Waltti router   | Yes (free)   |

## Dependencies

- `astral`: For solar calculations
- `ephem`: For lunar and eclipse calculations
- `requests`: For API calls
- `fmiopendata`: For Finnish Meteorological Institute data
- `timezonefinder`: For automatic timezone detection
- `holidays`: For international holiday calculations
- `entsoe`: For European electricity market data (optional, for enhanced electricity pricing)
- `pandas`: For data processing with entsoe (optional)

These are listed in `requirements.txt`.

## Example Output

```
📍 Turku, Suomi / Finland

Kello on noin kahdeksan (20.02), joten on myöhäisilta.
On perjantai, 9. tammikuuta, 2026.
...
Ajokeli: normaali
Sähkön hinta nyt: 14.44 c/kWh (15 min), 15.23 c/kWh (tunti)
Halvin sähkö: 18:15 (2.73 c/kWh). Kallein sähkö: 13:15 (7.56 c/kWh)
Revontuliennuste: Kp 2 (epätodennäköinen)
Seuraava auringonpimennys: 12.08.2026 (osittainen)
Seuraava kuunpimennys: 20.02.2027 (osittainen)

Liikenteen häiriöt:
  - Uudet liityntälinjat 27 ja 27A aloittavat liikennöinnin 7.1.2026
  - Linjan 615 aikataulumuutos 1.1.2026 alkaen

Huomisaamu (10.01): -11°c, pilvistä
Aurinko nousee klo 09.29

Varoitukset:
  ⚠️  Kylmävaroitus: kylmiä lämpötiloja, pukeudu lämpimästi
  ⚠️  Sähkövaroitus: kallis sähkö nyt (14.4 c/kWh)
```
