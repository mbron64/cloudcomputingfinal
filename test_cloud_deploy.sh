#!/bin/bash
# Test script for Cloud deployment (dry run)

set -e  # Exit on error

# Bold text function
bold() {
  echo -e "\033[1m$1\033[0m"
}

# Check if gcloud is installed
GCLOUD_INSTALLED=true
if ! command -v gcloud &> /dev/null; then
    GCLOUD_INSTALLED=false
    bold "WARNING: gcloud CLI not found. Running in simulation mode only."
fi

# Set up dummy values for dry run
export PROJECT_ID="beehive-test-project"
export REGION="us-central1"
export BUCKET_NAME="${PROJECT_ID}-beehive-data"
export DRY_RUN=true

bold "Testing cloud deployment (DRY RUN - no actual deployment)"
bold "Using the following configuration:"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Bucket Name: $BUCKET_NAME"
echo

bold "Creating temporary model file for testing..."
mkdir -p models
if [ ! -f "models/beehive_classifier.pkl" ]; then
    echo "Creating empty model file for testing..."
    touch models/beehive_classifier.pkl
fi

bold "Testing configuration and file creation..."

# Create cloud_function directory for testing
bold "Creating cloud_function directory..."
mkdir -p cloud_function
cp -r src/data cloud_function/ 2>/dev/null || echo "No data directory to copy"
mkdir -p src/cloud/function
touch src/cloud/function/main.py 2>/dev/null || echo "main.py already exists"
cp -r src/cloud/function/* cloud_function/ 2>/dev/null || echo "No function files to copy"

# Create requirements.txt for the Cloud Function
bold "Creating requirements.txt for Cloud Function..."
cat > cloud_function/requirements.txt <<EOL
google-cloud-storage==3.1.0
google-cloud-firestore==2.20.2
scikit-learn==1.6.1
joblib==1.5.0
numpy==2.2.5
EOL

# Create dashboard config
bold "Creating dashboard config..."
mkdir -p src/dashboard/config
cat > src/dashboard/config/dashboard_config.json <<EOL
{
  "use_firestore": true,
  "demo_mode": false,
  "refresh_interval": 5,
  "project_id": "$PROJECT_ID"
}
EOL

# Create temporary Dockerfile for testing
bold "Creating temporary Dockerfile..."
cat > Dockerfile.test <<EOL
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Create necessary directories
RUN mkdir -p /app/models /app/data /app/outputs /app/simulation_output

# Create config for cloud mode
RUN mkdir -p /app/src/dashboard/config
RUN echo '{"use_firestore": true, "demo_mode": false, "refresh_interval": 5, "project_id": "$PROJECT_ID"}' > /app/src/dashboard/config/dashboard_config.json

# Expose port
EXPOSE 8080

# Set the environment variables
ENV PORT=8080

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "src/dashboard/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
EOL

bold "Testing cloud function deployment command..."
echo "DRY RUN: Would execute: gcloud functions deploy beehive-processor \\"
echo "  --gen2 \\"
echo "  --region=$REGION \\"
echo "  --runtime=python39 \\"
echo "  --source=cloud_function \\"
echo "  --entry-point=process_audio \\"
echo "  --trigger-event=google.storage.object.finalize \\"
echo "  --trigger-resource=$BUCKET_NAME"

bold "Testing dashboard deployment command..."
echo "DRY RUN: Would execute: gcloud builds submit --tag gcr.io/$PROJECT_ID/beehive-dashboard"
echo "DRY RUN: Would execute: gcloud run deploy beehive-dashboard \\"
echo "  --image=gcr.io/$PROJECT_ID/beehive-dashboard \\"
echo "  --platform=managed \\"
echo "  --region=$REGION \\"
echo "  --allow-unauthenticated"

# Clean up temporary files
bold "Cleaning up temporary files..."
rm -f Dockerfile.test

bold "Cloud deployment test completed successfully!"
if ! $GCLOUD_INSTALLED; then
    echo "Note: This was a simulation run only, as gcloud CLI is not installed."
    echo "To perform an actual deployment:"
    echo "1. Install the Google Cloud SDK from: https://cloud.google.com/sdk/docs/install"
    echo "2. Run './deploy_cloud.sh'"
else
    echo "To perform an actual deployment, run ./deploy_cloud.sh"
fi 