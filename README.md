# Finnish Time Information Script

This script provides comprehensive time and date information in Finnish or English, including astronomical data, weather information, and environmental data.

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
- Daylight saving time information and next change countdown
- Next Finnish holiday calculation
- Weather warnings (cold, wind, precipitation, rain, snow, thunderstorms)
- Configurable language (Finnish or English)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

Or use the provided virtual environment:

1. The `.venv` directory contains all required dependencies
2. Run the script using the provided wrapper script

## Usage

### Direct execution:
```bash
python time_info_fi.py
```

### Using the wrapper script:
```bash
./run_time_info.sh
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

These are listed in `requirements.txt` and pre-installed in the `.venv` directory.