#!/bin/bash

# IoT Beehive Monitoring System Pipeline Script
# This script runs the entire pipeline from data processing to local simulation

set -e  # Exit on error

# Bold text function
bold() {
  echo -e "\033[1m$1\033[0m"
}

# Configuration
PYTHON_CMD=${PYTHON_CMD:-python}
MODE=${MODE:-local}  # Options: local, cloud

# Function to display usage
usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Options:"
  echo "  --explore      Run data exploration"
  echo "  --train        Train the model"
  echo "  --simulate     Simulate IoT devices"
  echo "  --dashboard    Run the dashboard"
  echo "  --cloud        Set mode to cloud (uses GCP services)"
  echo "  --local        Set mode to local (default)"
  echo "  --deploy       Deploy to Google Cloud Platform"
  echo "  --help         Show this help message"
}

# Parse command line arguments
EXPLORE=false
TRAIN=false
SIMULATE=false
DASHBOARD=false
DEPLOY=false

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --explore)
      EXPLORE=true
      shift
      ;;
    --train)
      TRAIN=true
      shift
      ;;
    --simulate)
      SIMULATE=true
      shift
      ;;
    --dashboard)
      DASHBOARD=true
      shift
      ;;
    --cloud)
      MODE="cloud"
      shift
      ;;
    --local)
      MODE="local"
      shift
      ;;
    --deploy)
      DEPLOY=true
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# If no options provided, run everything
if ! $EXPLORE && ! $TRAIN && ! $SIMULATE && ! $DASHBOARD && ! $DEPLOY; then
  EXPLORE=true
  TRAIN=true
  SIMULATE=true
  DASHBOARD=true
fi

echo "=========================================================="
echo "      IoT Beehive Monitoring System - Run Pipeline"
echo "=========================================================="
echo

# Check for Python environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Ensure dashboard dependencies are properly installed
echo "Ensuring dashboard dependencies are properly installed..."
pip install --upgrade --force-reinstall plotly==5.14.1
pip install --upgrade watchdog

# Create dashboard config for demo mode
echo "Setting up dashboard demo configuration..."
mkdir -p src/dashboard/config
echo '{
    "use_firestore": false,
    "demo_mode": true,
    "refresh_interval": 5
}' > src/dashboard/config/dashboard_config.json

touch venv/.packages_installed

# Create directory structure if it doesn't exist
echo "Setting up directory structure..."
mkdir -p data processed_data models outputs simulation_output

# Check if data exists
if [ ! -f "data/D1_sensor_data.csv" ] && [ ! -f "data/D2_sensor_data.csv" ]; then
    echo "Error: Data files not found in data/ directory."
    echo "Please ensure data files are available in the data directory before running this script."
    exit 1
fi

# Explore data
if $EXPLORE; then
  bold "Running data exploration..."
  $PYTHON_CMD scripts/explore_data.py || { echo "Error in data exploration step"; exit 1; }
  echo "Data exploration completed. Plots saved to outputs/ directory."
fi

# Train model
if $TRAIN; then
  bold "Training beehive behavior model..."
  $PYTHON_CMD scripts/train_basic_model.py || { echo "Error in model training step"; exit 1; }
  echo "Model training completed. Model saved to models/beehive_classifier.pkl"
fi

# Simulate IoT devices
if $SIMULATE; then
  bold "Simulating IoT devices..."
  if [ "$MODE" = "cloud" ]; then
    if [ -z "$PROJECT_ID" ]; then
      read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    fi
    BUCKET_NAME="${PROJECT_ID}-beehive-data"
    
    bold "Simulating IoT devices and uploading to GCS..."
    $PYTHON_CMD scripts/simulate_iot_uploads.py --cloud --bucket $BUCKET_NAME
  else
    $PYTHON_CMD scripts/simulate_iot_uploads.py
  fi
fi

# Run dashboard
if $DASHBOARD; then
  bold "Starting dashboard..."
  if [ "$MODE" = "cloud" ]; then
    # Create config for cloud mode if it doesn't exist
    mkdir -p src/dashboard/config
    if [ -z "$PROJECT_ID" ]; then
      read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    fi
    
    cat > src/dashboard/config/dashboard_config.json <<EOL
{
  "use_firestore": true,
  "demo_mode": false,
  "refresh_interval": 5,
  "project_id": "$PROJECT_ID"
}
EOL
  else
    # Create config for local mode if it doesn't exist
    mkdir -p src/dashboard/config
    cat > src/dashboard/config/dashboard_config.json <<EOL
{
  "use_firestore": false,
  "demo_mode": true,
  "refresh_interval": 5
}
EOL
  fi
  
  # Use the run_dashboard.sh script to start the dashboard
  if [ -x "./run_dashboard.sh" ]; then
    # Run in background
    ./run_dashboard.sh &
  else
    # Make script executable if needed
    chmod +x run_dashboard.sh
    ./run_dashboard.sh &
  fi
  
  echo "Dashboard is running at http://localhost:8501"
fi

# Deploy to GCP
if $DEPLOY; then
  bold "Deploying to Google Cloud Platform..."
  
  # Check if deploy_cloud.sh exists and is executable
  if [ ! -x "deploy_cloud.sh" ]; then
    chmod +x deploy_cloud.sh
  fi
  
  ./deploy_cloud.sh
fi

bold "Pipeline completed successfully!"
if $DASHBOARD; then
  echo "Dashboard is running at http://localhost:8501"
  echo "Press Ctrl+C to stop the dashboard when finished."
  wait
fi

# Test dashboard dependencies without starting it
echo "Checking dashboard dependencies..."
python -c "import streamlit, plotly.express, pandas, matplotlib, seaborn" || { 
    echo "==============================================================="
    echo "ERROR: Some dashboard dependencies are missing or not properly installed."
    echo "Run the following command to fix the dashboard dependencies:"
    echo "    ./install_dashboard_deps.sh"
    echo "==============================================================="
    exit 1
}

echo "Dashboard dependencies installed correctly!"
echo "If you still encounter issues with the dashboard, please run:"
echo "    ./install_dashboard_deps.sh"
echo
echo "To start the dashboard in demo mode, run:"
echo "    ./run_dashboard.sh"

echo
echo "=========================================================="
echo "Pipeline execution completed successfully!"
echo "===========================================================" 