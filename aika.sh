#!/bin/bash

# Script to activate virtual environment and run Aika
# Usage: ./aika.sh [location]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Activate the virtual environment
source "${SCRIPT_DIR}/.venv/bin/activate"

# Run Aika with location parameter if provided
if [ $# -gt 0 ]; then
	python -m aika "$@"
else
	python -m aika
fi

# Deactivate the virtual environment (optional, as the script will end anyway)
deactivate
