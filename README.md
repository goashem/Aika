# Aika: Time Information Script

This script provides comprehensive time and date information in Finnish or English, including astronomical data, weather
information, and environmental data.

## Features

- Time expressed in natural language (e.g., "nearly ten to two")
- Precise time-of-day terms (early morning, morning, forenoon, noon, afternoon, early evening, late evening, night)
- Date information with proper grammar
- Percentage of year completed (including time of day)
- Solar information (sunrise, sunset, elevation, azimuth)
- Lunar information (phase percentage, growth status, elevation, azimuth)
- Weather information (temperature, humidity, pressure, wind) - uses FMI as primary source with Open-Meteo fallback
- Environmental data (air quality index, UV index)
- Seasonal information with automatic hemisphere detection
- Next holiday calculation with automatic country detection
- Weather warnings (cold, wind, precipitation, rain, snow, thunderstorms)
- Configurable language (Finnish or English)
- Support for location-based timezones
- Solar radiation data for solar panel owners
- Marine data (wave height, direction, period)
- Flood/rain data (river discharge)
- Morning weather forecasts
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

## Dependencies

- `astral`: For solar calculations
- `ephem`: For lunar calculations
- `requests`: For weather API calls
- `fmiopendata`: For Finnish Meteorological Institute data
- `timezonefinder`: For automatic timezone detection
- `holidays`: For international holiday calculations

These are listed in `requirements.txt`.