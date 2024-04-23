#!/bin/bash

# Change to root directory
cd || exit

# Change directory to the specified path
cd ./Downloads/project/Voice_assist/code || exit

# Activate the virtual environment
source ../venv/bin/activate || exit

# Function to deactivate virtual environment and return to main directory
cleanup() {
    deactivate 2>/dev/null || true
    cd - >/dev/null || true
}

# Trap CTRL+C and call cleanup function
trap cleanup INT

# Execute the Python script
python assist.py

# Call cleanup function after Python script exits
cleanup