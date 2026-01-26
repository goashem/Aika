# Aika - Enhanced Weather Information Application

Aika is a comprehensive weather information tool for Finland and Nordic countries that provides detailed meteorological data including time, astronomical information, weather forecasts, transportation disruptions, and environmental conditions.

## New Features Added

### 1. Enhanced Lightning/Thunderstorm Detection System
- Detailed threat level assessment with immediate danger warnings
- Directional tracking of approaching storms
- Peak current strength indicators for severe strikes
- Year-round detection including thundersnow phenomena

### 2. Comprehensive Pollen Forecast Integration
- Species-specific pollen levels (birch, grass, alder, mugwort, ragweed)
- Finnish pollen type names (koivu, heinä, leppä, pujo, tuoksukki)
- Seasonal adjustments (winter-appropriate low levels in January)
- Personalized allergy recommendations based on pollen concentrations
- Integration with existing warning system

### 3. UV Index Forecasting with Skin Protection
- Personalized burn time calculations based on Fitzpatrick skin types
- Category-based protection recommendations
- Safe exposure time guidance
- Peak UV timing information
- Enhanced UV display in both Finnish and English

## Usage

```bash
python3 -m aika "Location Name"
```

Example:
```bash
python3 -m aika "Helsinki"
python3 -m aika --lang en "Espoo"
```

## Features

### Time Information
- Current time with descriptive expressions
- Date, week number, and day of year
- Local time vs. system time differences

### Astronomical Data
- Sunrise, sunset, dawn, dusk times
- Solar noon and daylight duration
- Golden hour and blue hour indicators
- Moon phase, rise/set times, and future phases
- Eclipse information

### Weather Information
- Current temperature and "feels like" temperature
- Weather description and precipitation probability
- Wind speed, direction, and gust information
- Humidity, pressure, and visibility
- Wave height, period, and direction for coastal areas
- Sea water temperature and ice cover

### Forecasts
- Short-term precipitation nowcast (next 2 hours)
- 12-hour detailed forecast
- 7-day extended forecast with recommendations

### Environmental Data
- Air quality index (AQI)
- UV index with personalized protection advice
- Flood risk assessment with river discharge data
- Road weather conditions (Finland only)
- Aurora borealis forecast (Finland only)

### Finnish-Specific Features
- Electricity prices and CO₂ emission levels
- Transportation disruptions for Helsinki region
- Detailed pollen forecasts with Finnish names
- Enhanced lightning/thunderstorm detection

### Warnings
- Temperature extremes (-30°C and below)
- High wind advisories (15+ m/s)
- Precipitation probability warnings
- Weather code-based warnings (rain, snow, thunderstorms)
- UV warnings (index 6+)
- Air quality warnings (AQI 4+)
- Lightning warnings with threat levels
- Pollen warnings for allergy sufferers
- Road condition warnings
- Electricity price warnings

## Installation

1. Clone the repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python3 -m aika "Your Location"
   ```

## Configuration

Create a `config.ini` file or let the application prompt you for your location preferences.

## Data Sources

- Finnish Meteorological Institute (FMI) Open Data
- Open-Meteo API for international locations
- Finnish Transport Infrastructure Agency (Fintraffic)
- Entso-E for electricity price data (Finland)
- SILAM model for pollen forecasts (simulated in current implementation)

## License

MIT License