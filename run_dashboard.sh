#!/bin/bash

# Exit on error
set -e

# Clear terminal
clear

echo "=========================================================="
echo "      Beehive Monitoring Dashboard Launcher"
echo "=========================================================="
echo

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found, proceeding with system Python..."
fi

# Check if required packages are installed
echo "Checking required packages..."
missing_packages=false

# Check for plotly
if ! python -c "import plotly" &>/dev/null; then
    echo "- Plotly not found"
    missing_packages=true
fi

# Check for streamlit
if ! python -c "import streamlit" &>/dev/null; then
    echo "- Streamlit not found"
    missing_packages=true
fi

# Install missing packages if needed
if [ "$missing_packages" = true ]; then
    echo "Installing missing packages..."
    pip install plotly streamlit pandas matplotlib
fi

# Set up dashboard configuration
echo "Setting up dashboard in demo mode..."
mkdir -p src/dashboard/config
cat > src/dashboard/config/dashboard_config.json <<EOL
{
    "use_firestore": false,
    "demo_mode": true,
    "refresh_interval": 5,
    "project_id": "your-project-id"
}
EOL

# Check if we have simulation data
if [ ! -d "simulation_output" ] || [ -z "$(ls -A simulation_output 2>/dev/null)" ]; then
    echo "No simulation data found. Generating sample data..."
    mkdir -p simulation_output
    
    # Generate some sample data if the simulator script exists
    if [ -f "scripts/simulate_iot_uploads.py" ]; then
        python scripts/simulate_iot_uploads.py --devices 3 --samples 5
    fi
fi

echo "Starting the dashboard..."
echo "Press Ctrl+C to stop the dashboard when finished."
echo "=========================================================="
python -m streamlit run src/dashboard/app.py 