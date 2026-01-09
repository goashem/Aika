#!/bin/bash

# Script to activate virtual environment and run the Finnish time info script
# Usage: ./run_time_info.sh [location]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Activate the virtual environment
source "${SCRIPT_DIR}/.venv/bin/activate"

# Run the Finnish time info script with location parameter if provided
if [ $# -gt 0 ]; then
	python "${SCRIPT_DIR}/time_info_fi.py" "$@"
else
	python "${SCRIPT_DIR}/time_info_fi.py"
fi

# Deactivate the virtual environment (optional, as the script will end anyway)
deactivate
