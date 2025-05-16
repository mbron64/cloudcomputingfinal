#!/bin/bash

# Script to ensure dashboard dependencies are properly installed
echo "Installing dashboard dependencies..."

# Make script executable
chmod +x install_dashboard_deps.sh

# Ensure we're using the correct environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Using virtual environment in venv/"
else
    echo "No virtual environment found. Installing globally (not recommended)"
fi

# Force reinstall plotly and its dependencies
pip install --upgrade --force-reinstall plotly
pip install --upgrade streamlit

# Optional but recommended for performance
echo "Installing watchdog for better Streamlit performance..."
pip install watchdog

echo "Dashboard dependencies installed successfully."
echo "Now run 'streamlit run src/dashboard/app.py' to start the dashboard." 