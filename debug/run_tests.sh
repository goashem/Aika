#!/bin/bash

# Script to run all debug tests

echo "Running all debug tests..."
echo "=========================="

# Run the specific time test
echo "1. Testing ground truth data at specific time:"
python test_specific_time.py

echo ""
echo "All tests completed!"
