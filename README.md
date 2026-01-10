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

- Weather information (temperature, humidity, pressure, wind) - uses FMI as the primary source with Open-Meteo fallback
- Environmental data (air quality index, UV index)
- Marine data (wave height, direction, period)
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

- **Road weather (Ajokeli)** - Driving conditions from Fintraffic Digitraffic API
- **Electricity price** - Current spot price from Porssisahko.net (c/kWh)
- **Aurora forecast** - Kp-index from NOAA SWPC and FMI
- **Public transport disruptions**:
  - Turku area: Foli API (no API key needed)
  - Helsinki area: Digitransit HSL (requires free API key)
  - Other areas: Digitransit Finland (requires free API key)

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

## Package Structure

```
aika/
├── __init__.py      # Package entry point
├── __main__.py      # CLI entry (python -m aika)
├── core.py          # Main TimeInfo coordinator class
├── config.py        # Configuration management
├── geolocation.py   # Geocoding and timezone detection
├── weather.py       # Weather data from FMI and Open-Meteo
├── astronomy.py     # Sun/moon calculations and eclipses
├── calendar_info.py # Seasons, holidays, date calculations
├── finland.py       # Road weather, electricity, aurora, transit
├── localization.py  # Translations and time expressions
└── display.py       # Output formatting
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

| Warning                      | Threshold  |
|------------------------------|------------|
| Cold (moderate)              | <= -10C    |
| Cold (severe)                | <= -20C    |
| Cold (extreme)               | <= -30C    |
| Wind (advisory)              | >= 15 m/s  |
| Wind (high)                  | >= 25 m/s  |
| Electricity (expensive)      | >= 12 c/kWh|
| Electricity (very expensive) | >= 18 c/kWh|

## Data Sources

| Data              | Source                     | Requires Key |
|-------------------|----------------------------|--------------|
| Weather           | FMI Open Data / Open-Meteo | No           |
| Air Quality       | Open-Meteo                 | No           |
| Road Weather      | Fintraffic Digitraffic     | No           |
| Electricity Price | Porssisahko.net            | No           |
| Aurora (Kp)       | NOAA SWPC / FMI            | No           |
| Eclipses          | Calculated with ephem      | No (offline) |
| Transport (Turku) | Foli API                   | No           |
| Transport (other) | Digitransit                | Yes (free)   |

## Dependencies

- `astral`: For solar calculations
- `ephem`: For lunar and eclipse calculations
- `requests`: For API calls
- `fmiopendata`: For Finnish Meteorological Institute data
- `timezonefinder`: For automatic timezone detection
- `holidays`: For international holiday calculations

These are listed in `requirements.txt`.

## Example Output

```
📍 Turku, Suomi / Finland

Kello on noin kahdeksan (20.02), joten on myöhäisilta.
On perjantai, 9. tammikuuta, 2026.
...
Ajokeli: normaali
Sähkön hinta nyt: 14.44 c/kWh
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
