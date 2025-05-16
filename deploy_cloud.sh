#!/bin/bash

# Exit on error
set -e

# Bold text function
bold() {
  echo -e "\033[1m$1\033[0m"
}

# Set variables (modify these according to your needs)
if [ -z "$PROJECT_ID" ]; then
  read -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi

if [ -z "$REGION" ]; then
  REGION="us-central1"
fi

BUCKET_NAME="${PROJECT_ID}-beehive-data"
FUNCTION_NAME="beehive-processor"
DASHBOARD_NAME="beehive-dashboard"

# Confirmation
echo "This script will deploy the Beehive Monitoring System to Google Cloud."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Deployment cancelled."
  exit 1
fi

# Ensure gcloud is configured to use the right project
bold "Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
bold "Enabling required APIs..."
gcloud services enable cloudfunctions.googleapis.com \
                       run.googleapis.com \
                       firestore.googleapis.com \
                       storage.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com

# Create Cloud Storage bucket
bold "Creating Cloud Storage bucket..."
gsutil mb -l $REGION gs://$BUCKET_NAME || {
  echo "Bucket already exists or error creating bucket."
}

# Upload model to bucket
bold "Uploading ML model to bucket..."
gsutil cp models/beehive_classifier.pkl gs://$BUCKET_NAME/models/beehive_classifier.pkl || {
  echo "Error uploading model. Make sure the model file exists."
  exit 1
}

# Create Firestore database if not exists
bold "Setting up Firestore..."
gcloud firestore databases create --region=$REGION || {
  echo "Firestore database already exists or error creating database."
}

# Create a service account for the function if it doesn't exist
bold "Setting up service account..."
SERVICE_ACCOUNT="${FUNCTION_NAME}-sa"
gcloud iam service-accounts create $SERVICE_ACCOUNT --display-name="Beehive Processor Service Account" || {
  echo "Service account already exists or error creating service account."
}

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Create cloud_function directory if it doesn't exist
bold "Preparing Cloud Function deployment..."
mkdir -p cloud_function
cp -r src/data cloud_function/
cp -r src/cloud/function/* cloud_function/

# Create Cloud Function main.py if it doesn't exist
if [ ! -f cloud_function/main.py ]; then
  cat > cloud_function/main.py <<EOL
import json
import joblib
import numpy as np
from google.cloud import storage
from google.cloud import firestore

# Load the model (will download from bucket in the actual function)
# model = joblib.load('path_to_model')

def process_audio(event, context):
    """Cloud Function triggered by a Cloud Storage event.
    Args:
        event (dict): Event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    print(f"Processing file: {event['name']}")
    
    # Only process JSON files in the beehive data directory
    if not event['name'].endswith('.json'):
        print(f"Ignoring non-JSON file: {event['name']}")
        return
    
    # Extract data from the GCS event
    bucket_name = event['bucket']
    file_path = event['name']
    
    # Get the file from GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    content = blob.download_as_string()
    data = json.loads(content)
    
    # Process the data (in a real implementation, you'd extract features here)
    prediction = "normal"
    confidence = 0.95
    
    # Update Firestore
    db = firestore.Client()
    doc_ref = db.collection('hive_events').document()
    doc_ref.set({
        'timestamp': context.timestamp,
        'device_id': data.get('device_id', 'unknown'),
        'behavior': prediction,
        'confidence': confidence,
        'source_file': f"gs://{bucket_name}/{file_path}"
    })
    
    print(f"Processed file {file_path}. Prediction: {prediction}")
    return "Success"
EOL
fi

# Create requirements.txt for the Cloud Function
cat > cloud_function/requirements.txt <<EOL
google-cloud-storage==3.1.0
google-cloud-firestore==2.20.2
scikit-learn==1.6.1
joblib==1.5.0
numpy==2.2.5
EOL

# Deploy Cloud Function
bold "Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --region=$REGION \
  --runtime=python39 \
  --source=cloud_function \
  --entry-point=process_audio \
  --trigger-event=google.storage.object.finalize \
  --trigger-resource=$BUCKET_NAME \
  --service-account=${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com

# Build and deploy the dashboard to Cloud Run
bold "Building and deploying dashboard to Cloud Run..."

# Create a temporary Dockerfile for the dashboard
cat > Dockerfile <<EOL
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

# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/$DASHBOARD_NAME

gcloud run deploy $DASHBOARD_NAME \
  --image=gcr.io/$PROJECT_ID/$DASHBOARD_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated

# Clean up temporary files
rm Dockerfile

bold "Deployment complete!"
echo "Your beehive monitoring system is now deployed to Google Cloud."
echo "Dashboard URL: $(gcloud run services describe $DASHBOARD_NAME --platform=managed --region=$REGION --format='value(status.url)')"
echo
echo "To upload data to the system, use the following command:"
echo "  gsutil cp your_data_file.json gs://$BUCKET_NAME/"
echo
echo "This will automatically trigger the Cloud Function to process the data."

# Optional: Upload a sample file to GCS to test the function
if [ -d "simulation_output" ] && [ "$(ls -A simulation_output)" ]; then
  read -p "Upload a sample file to test the system? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    SAMPLE_FILE=$(ls simulation_output/*.json | head -n 1)
    if [ ! -z "$SAMPLE_FILE" ]; then
      bold "Uploading sample file to GCS..."
      gsutil cp $SAMPLE_FILE gs://$BUCKET_NAME/
      echo "Sample file uploaded. Check the Cloud Function logs for processing status."
    else
      echo "No sample files found in simulation_output directory."
    fi
  fi
fi 