#!/usr/bin/env python3
"""
Test file for astronomical calculations validation
Base data for January 9, 2026, 14:16 Finnish time at "Puistokatu 12, Turku, Finland"
Ground truth data provided by user.
"""

# Ground truth values for validation
GROUND_TRUTH_VALUES = {
    'date_time': '2026-01-09 14:16:00',
    'location': 'Puistokatu 12, Turku, Finland',
    'coordinates': {
        'latitude': 60.4477801,
        'longitude': 22.2503515
    },
    'sun': {
        'altitude': 5.6,
        'azimuth': 202.7,
        'dawn_start': '08:34',
        'sunrise': '09:30',
        'solar_noon': '12:37',
        'sunset': '15:45',
        'dusk_end': '16:41'
    },
    'moon': {
        'altitude': -23.6,
        'azimuth': 304.8,
        'illumination_percent': 61.3,
        'rise_time': '00:43',
        'peak_time': '05:51',
        'set_time': '10:59'
    }
}

# Test tolerance (acceptable error margins)
TEST_TOLERANCE = {
    'sun_altitude': 0.5,      # degrees
    'sun_azimuth': 1.0,       # degrees
    'moon_altitude': 1.0,     # degrees
    'moon_azimuth': 1.0,      # degrees
    'moon_illumination': 1.0, # percent
    'time_minutes': 5         # minutes
}

def validate_sun_position(calculated_altitude, calculated_azimuth):
    """Validate sun position against ground truth values"""
    expected_alt = GROUND_TRUTH_VALUES['sun']['altitude']
    expected_az = GROUND_TRUTH_VALUES['sun']['azimuth']
    
    alt_diff = abs(calculated_altitude - expected_alt)
    az_diff = abs(calculated_azimuth - expected_az)
    
    alt_pass = alt_diff <= TEST_TOLERANCE['sun_altitude']
    az_pass = az_diff <= TEST_TOLERANCE['sun_azimuth']
    
    return {
        'altitude': {
            'expected': expected_alt,
            'calculated': calculated_altitude,
            'difference': alt_diff,
            'pass': alt_pass
        },
        'azimuth': {
            'expected': expected_az,
            'calculated': calculated_azimuth,
            'difference': az_diff,
            'pass': az_pass
        },
        'overall_pass': alt_pass and az_pass
    }

def validate_moon_position(calculated_altitude, calculated_azimuth, calculated_illumination):
    """Validate moon position against ground truth values"""
    expected_alt = GROUND_TRUTH_VALUES['moon']['altitude']
    expected_az = GROUND_TRUTH_VALUES['moon']['azimuth']
    expected_illum = GROUND_TRUTH_VALUES['moon']['illumination_percent']
    
    alt_diff = abs(calculated_altitude - expected_alt)
    az_diff = abs(calculated_azimuth - expected_az)
    illum_diff = abs(calculated_illumination - expected_illum)
    
    alt_pass = alt_diff <= TEST_TOLERANCE['moon_altitude']
    az_pass = az_diff <= TEST_TOLERANCE['moon_azimuth']
    illum_pass = illum_diff <= TEST_TOLERANCE['moon_illumination']
    
    return {
        'altitude': {
            'expected': expected_alt,
            'calculated': calculated_altitude,
            'difference': alt_diff,
            'pass': alt_pass
        },
        'azimuth': {
            'expected': expected_az,
            'calculated': calculated_azimuth,
            'difference': az_diff,
            'pass': az_pass
        },
        'illumination': {
            'expected': expected_illum,
            'calculated': calculated_illumination,
            'difference': illum_diff,
            'pass': illum_pass
        },
        'overall_pass': alt_pass and az_pass and illum_pass
    }

if __name__ == "__main__":
    print("Ground truth data loaded for validation:")
    print(f"Date/Time: {GROUND_TRUTH_VALUES['date_time']}")
    print(f"Location: {GROUND_TRUTH_VALUES['location']}")
    print(f"Sun altitude: {GROUND_TRUTH_VALUES['sun']['altitude']}°")
    print(f"Sun azimuth: {GROUND_TRUTH_VALUES['sun']['azimuth']}°")
    print(f"Moon altitude: {GROUND_TRUTH_VALUES['moon']['altitude']}°")
    print(f"Moon azimuth: {GROUND_TRUTH_VALUES['moon']['azimuth']}°")
    print(f"Moon illumination: {GROUND_TRUTH_VALUES['moon']['illumination_percent']}%")