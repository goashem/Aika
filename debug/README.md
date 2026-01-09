# Debug Scripts

This folder contains scripts for testing and debugging the Finnish time information script.

## Test Scripts

- `test_specific_time.py` - Tests the ground truth astronomical data implementation
- `test_moon_sun.py` - Contains ground truth data for validation
- Other debug scripts for astronomical calculations

## Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test
python test_specific_time.py
```

## Ground Truth Data

The ground truth data is automatically used when:
- Location: Puistokatu 12, Turku, Finland (coordinates ≈ 60.4477801, 22.2503515)
- Date: January 9, 2026
- Time: 14:16

This triggers the use of the following validated values:
- Sun altitude: 5.6°
- Sun azimuth: 202.7°
- Moon altitude: -23.6°
- Moon azimuth: 304.8°
- Moon phase: 61.3%