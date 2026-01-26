#!/bin/bash

# Setup script for Aika conda environment
# This script creates and configures the conda environment for Aika
# Works on Linux, macOS, and Windows (Git Bash/WSL)

set -e # Exit on any error

echo "Setting up Aika conda environment..."

# Function to detect OS and set appropriate variables
detect_os() {
	case "$(uname -s)" in
	Darwin*)
		# macOS
		OS_TYPE="macOS"
		CONDA_INSTALL_PATH="$HOME/miniconda3"
		if [ "$(uname -m)" == "arm64" ]; then
			CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
		else
			CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
		fi
		;;
	Linux*)
		# Linux
		OS_TYPE="Linux"
		CONDA_INSTALL_PATH="$HOME/miniconda3"
		CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh"
		;;
	CYGWIN* | MINGW* | MSYS*)
		# Windows (Git Bash)
		OS_TYPE="Windows"
		CONDA_INSTALL_PATH="/c/Users/$(whoami)/miniconda3"
		CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
		echo "Windows detected. Please install Miniconda manually from https://docs.anaconda.com/miniconda/"
		exit 1
		;;
	*)
		# Default
		OS_TYPE="Unknown"
		CONDA_INSTALL_PATH="$HOME/miniconda3"
		CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-$(uname)-$(uname -m).sh"
		;;
	esac
}

detect_os

# Check if conda is installed
if ! command -v conda &>/dev/null; then
	echo "Conda not found. Installing Miniconda for $OS_TYPE..."

	# For Windows, we can't automate the installation
	if [ "$OS_TYPE" == "Windows" ]; then
		echo "Please install Miniconda manually for Windows:"
		echo "1. Download from: https://docs.anaconda.com/miniconda/"
		echo "2. Run the installer and follow the prompts"
		echo "3. Restart your terminal/command prompt"
		echo "4. Run this script again"
		exit 1
	fi

	# Download and install Miniconda for Linux/macOS
	curl -O $CONDA_URL
	bash $(basename $CONDA_URL) -b -p $CONDA_INSTALL_PATH
	rm $(basename $CONDA_URL)

	# Initialize conda
	$CONDA_INSTALL_PATH/bin/conda init bash
	$CONDA_INSTALL_PATH/bin/conda init zsh

	# Source conda
	source "$CONDA_INSTALL_PATH/etc/profile.d/conda.sh"
else
	echo "Conda found. Checking environment..."
	source "$CONDA_INSTALL_PATH/etc/profile.d/conda.sh" 2>/dev/null || true

	# Handle case where miniconda exists but conda command is not in PATH
	if ! conda info &>/dev/null; then
		source "$CONDA_INSTALL_PATH/etc/profile.d/conda.sh"
	fi
fi

# Check if the aika environment exists
if conda info --envs | grep -q "^aika "; then
	echo "Aika conda environment already exists."
else
	echo "Creating Aika conda environment..."
	conda create -n aika python=3.11 -y

	# Accept ToS if needed
	conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
	conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true
fi

# Activate the environment
conda activate aika

# Install requirements
echo "Installing required packages..."
pip install -r requirements.txt

echo "Setup complete! You can now run Aika with ./aika.sh"
