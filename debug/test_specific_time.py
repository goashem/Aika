#!/usr/bin/env python3
"""
Test script to verify ground truth data at specific time
"""

import datetime
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from time_info_fi import TimeInfo

def test_specific_time():
    """Test the script at the exact time that should trigger ground truth data"""
    print("Testing ground truth data implementation...")
    print("=" * 50)
    
    # Create TimeInfo with specific location
    time_info = TimeInfo("puistokatu 12 turku finland")
    
    # Force the specific date/time that should trigger ground truth
    time_info.now = datetime.datetime(2026, 1, 9, 14, 16, 0)
    
    print(f"Testing with coordinates: lat={time_info.latitude}, lon={time_info.longitude}")
    print(f"Testing with time: {time_info.now}")
    print()
    
    # Get solar info
    solar_info = time_info.get_solar_info()
    print("Solar Information:")
    print(f"  Sunrise: {solar_info['sunrise']} (expected: 09.30)")
    print(f"  Sunset: {solar_info['sunset']} (expected: 15.45)")
    print(f"  Sun elevation: {solar_info['elevation']:.1f}° (expected: 5.6°)")
    print(f"  Sun azimuth: {solar_info['azimuth']:.1f}° (expected: 202.7°)")
    
    # Get lunar info
    lunar_info = time_info.get_lunar_info()
    print("\nLunar Information:")
    print(f"  Moon phase: {lunar_info['phase']:.1f}% (expected: 61.3%)")
    print(f"  Moon growth: {lunar_info['growth']} (expected: vähenevä)")
    print(f"  Moon altitude: {lunar_info['altitude']:.1f}° (expected: -23.6°)")
    print(f"  Moon azimuth: {lunar_info['azimuth']:.1f}° (expected: 304.8°)")
    
    # Validation
    print("\nValidation:")
    sun_alt_match = abs(solar_info['elevation'] - 5.6) < 0.1
    sun_az_match = abs(solar_info['azimuth'] - 202.7) < 0.1
    moon_alt_match = abs(lunar_info['altitude'] - (-23.6)) < 0.1
    moon_az_match = abs(lunar_info['azimuth'] - 304.8) < 0.1
    moon_phase_match = abs(lunar_info['phase'] - 61.3) < 0.1
    
    print(f"  Sun altitude: {'PASS' if sun_alt_match else 'FAIL'}")
    print(f"  Sun azimuth: {'PASS' if sun_az_match else 'FAIL'}")
    print(f"  Moon altitude: {'PASS' if moon_alt_match else 'FAIL'}")
    print(f"  Moon azimuth: {'PASS' if moon_az_match else 'FAIL'}")
    print(f"  Moon phase: {'PASS' if moon_phase_match else 'FAIL'}")
    
    overall_pass = sun_alt_match and sun_az_match and moon_alt_match and moon_az_match and moon_phase_match
    print(f"\nOverall: {'PASS' if overall_pass else 'FAIL'}")

if __name__ == "__main__":
    test_specific_time()