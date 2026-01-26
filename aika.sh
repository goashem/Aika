#!/bin/bash

# Script to activate conda environment and run Aika
# Works on Linux, macOS, and Windows (Git Bash/WSL)
# Usage: ./aika.sh [location]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Function to detect OS and set appropriate paths
detect_os() {
	case "$(uname -s)" in
	Darwin*)
		# macOS
		OS_TYPE="macOS"
		CONDA_PATH="$HOME/miniconda3/etc/profile.d/conda.sh"
		INSTALL_CMD='curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-$(uname -m).sh -o miniconda.sh && bash miniconda.sh'
		;;
	Linux*)
		# Linux
		OS_TYPE="Linux"
		CONDA_PATH="$HOME/miniconda3/etc/profile.d/conda.sh"
		INSTALL_CMD='curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh -o miniconda.sh && bash miniconda.sh'
		;;
	CYGWIN* | MINGW* | MSYS*)
		# Windows (Git Bash)
		OS_TYPE="Windows"
		CONDA_PATH="$USERPROFILE/miniconda3/etc/profile.d/conda.sh"
		# Convert to Unix path if needed
		if [ -f "/c/ProgramData/Anaconda3/etc/profile.d/conda.sh" ]; then
			CONDA_PATH="/c/ProgramData/Anaconda3/etc/profile.d/conda.sh"
		elif [ -f "/c/Users/$(whoami)/miniconda3/etc/profile.d/conda.sh" ]; then
			CONDA_PATH="/c/Users/$(whoami)/miniconda3/etc/profile.d/conda.sh"
		fi
		INSTALL_CMD='Download from https://docs.anaconda.com/miniconda/'
		;;
	*)
		# Default path
		OS_TYPE="Unknown"
		CONDA_PATH="$HOME/miniconda3/etc/profile.d/conda.sh"
		INSTALL_CMD='curl https://repo.anaconda.com/miniconda/Miniconda3-latest-$(uname)-$(uname -m).sh -o miniconda.sh && bash miniconda.sh'
		;;
	esac
}

# Function to check if conda environment exists
check_conda_env() {
	detect_os

	# Try to source conda silently
	if [ -f "$CONDA_PATH" ]; then
		source "$CONDA_PATH" 2>/dev/null || true
	fi

	# Check if conda command exists and environment exists
	if command -v conda &>/dev/null; then
		if conda info --envs 2>/dev/null | grep -q "^aika "; then
			return 0
		fi
		return 1
	else
		return 1
	fi
}

# Check if conda environment exists, if not create it
if ! check_conda_env; then
	echo "Aika conda environment not found. Setting it up..."
	"$SCRIPT_DIR/setup_conda.sh"

	# Source conda after setup
	detect_os
	if [ -f "$CONDA_PATH" ]; then
		source "$CONDA_PATH"
	fi
fi

# Initialize conda
detect_os
if [ -f "$CONDA_PATH" ]; then
	source "$CONDA_PATH"
else
	echo "Error: Conda not found. Please install conda first:"
	echo ""
	echo "For $OS_TYPE:"
	echo "  $INSTALL_CMD"
	echo ""
	echo "After installation, please restart your terminal and run this script again."
	exit 1
fi

# Activate the conda environment
if command -v conda &>/dev/null; then
	conda activate aika
else
	echo "Error: Conda command not available. Please ensure conda is properly installed."
	echo "For $OS_TYPE, try restarting your terminal after conda installation."
	exit 1
fi

# Run Aika with location parameter if provided
if [ $# -gt 0 ]; then
	python -m aika "$@"
else
	python -m aika
fi

# Deactivate the conda environment (optional, as the script will end anyway)
conda deactivate 2>/dev/null || true
