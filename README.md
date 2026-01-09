# Finnish Time Info Script

This script provides comprehensive time and date information in Finnish, including solar and lunar data.

## Features

- Time expressed in natural Finnish (e.g., "noin kymmentä vaille kaksi")
- Precise Finnish time-of-day terms (aamupäivä, iltapäivä, etc.)
- Date information in Finnish with proper grammar
- Percentage of year completed (including time of day)
- Solar information (sunrise, sunset, elevation, azimuth)
- Lunar information (phase percentage, growth status, elevation, azimuth)

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

Location settings can be adjusted in `config.ini`:
- `latitude`: Geographic latitude
- `longitude`: Geographic longitude
- `timezone`: Timezone identifier

## Dependencies

- `astral`: For solar calculations
- `ephem`: For lunar calculations

These are listed in `requirements.txt` and pre-installed in the `.venv` directory.