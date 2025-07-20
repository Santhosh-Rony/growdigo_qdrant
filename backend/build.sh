#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables for production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Build completed successfully!" 