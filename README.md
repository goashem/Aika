# Aika: Time Information Script

This script provides comprehensive time and date information in Finnish or English, including astronomical data, weather
information, and environmental data.

## Features

### Time & Date
- Time expressed in natural language (e.g., "nearly ten to two")
- Precise time-of-day terms (early morning, morning, forenoon, noon, afternoon, early evening, late evening, night)
- Date information with proper grammar
- Percentage of year completed (including time of day)
- Seasonal information with automatic hemisphere detection
- Next holiday calculation with automatic country detection

### Astronomy
- Solar information (dawn, sunrise, noon, sunset, dusk, elevation, azimuth)
- Lunar information (phase percentage, growth status, elevation, azimuth, rise/set times)
- Next solar eclipse (date and type - offline calculation)
- Next lunar eclipse (date and type - offline calculation)
- Solar radiation data for solar panel owners

### Weather
- Weather information (temperature, humidity, pressure, wind) - uses FMI as primary source with Open-Meteo fallback
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
- **Public transport disruptions** - From Digitransit API (requires API key)

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

1. The `.venv` directory, install the dependencies there.
2. Run the script using the wrapper script

## Usage

### Direct execution:

```bash
python time_info_fi.py
```

### Using the wrapper script:

```bash
./run_time_info.sh
```

### With location parameter:

```bash
./run_time_info.sh "Helsinki"
python time_info_fi.py "New York"
```

## Configuration

Location and language settings can be adjusted in `config.ini`:

- `latitude`: Geographic latitude
- `longitude`: Geographic longitude
- `timezone`: Timezone identifier
- `language`: Language preference (fi or en)

### API Keys

Some features require API keys:

- **Digitransit** (public transport disruptions): Register at [digitransit.fi](https://digitransit.fi/en/developers/api-registration/) to get a free API key. Add it to the `get_transport_disruptions()` method.

### Warning Thresholds

Default warning thresholds (can be modified in the code):

| Warning | Threshold |
|---------|-----------|
| Cold (moderate) | ≤ -10°C |
| Cold (severe) | ≤ -20°C |
| Cold (extreme) | ≤ -30°C |
| Wind (advisory) | ≥ 15 m/s |
| Wind (high) | ≥ 25 m/s |
| Electricity (expensive) | ≥ 12 c/kWh |
| Electricity (very expensive) | ≥ 18 c/kWh |

## Data Sources

| Data | Source | Requires Key |
|------|--------|--------------|
| Weather | FMI Open Data / Open-Meteo | No |
| Air Quality | Open-Meteo | No |
| Road Weather | Fintraffic Digitraffic | No |
| Electricity Price | Porssisahko.net | No |
| Aurora (Kp) | NOAA SWPC / FMI | No |
| Eclipses | Calculated with ephem | No (offline) |
| Transport | Digitransit | Yes (free) |

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
Kello on noin kahdeksan (20.02), joten on myöhäisilta.
On perjantai, 9. tammikuuta, 2026.
...
Ajokeli: normaali
Sähkön hinta nyt: 14.44 c/kWh
Revontuliennuste: Kp 2 (epätodennäköinen)
Seuraava auringonpimennys: 17.02.2026 (osittainen)
Seuraava kuunpimennys: 03.03.2026 (täydellinen)

Huomisaamu (10.01): -11°c, pilvistä
Aurinko nousee klo 09.29

Varoitukset:
  ⚠️  Kylmävaroitus: kylmiä lämpötiloja, pukeudu lämpimästi
  ⚠️  Sähkövaroitus: kallis sähkö nyt (14.4 c/kWh)
```