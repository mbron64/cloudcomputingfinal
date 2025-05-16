#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
BUCKET_NAME=${BUCKET_NAME:-"beehive-audio-bucket"}
FUNCTION_NAME="process_beehive_audio"
RUNTIME="python310"
SOURCE_DIR="src/cloud/function"
ENTRY_POINT="process_event"
MEMORY="256MB"
TIMEOUT="60s"

# Display configuration
echo "========== Deployment Configuration =========="
echo "Project ID:    $PROJECT_ID"
echo "Region:        $REGION"
echo "Bucket:        $BUCKET_NAME"
echo "Function name: $FUNCTION_NAME"
echo "Runtime:       $RUNTIME"
echo "Source:        $SOURCE_DIR"
echo "Entry point:   $ENTRY_POINT"
echo "Memory:        $MEMORY"
echo "Timeout:       $TIMEOUT"
echo "==========================================="
echo

# Check if the bucket exists, create if not
echo "Checking if bucket exists..."
if ! gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    echo "Creating bucket gs://$BUCKET_NAME"
    gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME
else
    echo "Bucket gs://$BUCKET_NAME already exists"
fi

# Create model directory if it doesn't exist
if [ ! -d "$SOURCE_DIR/model" ]; then
    echo "Creating model directory in function source"
    mkdir -p "$SOURCE_DIR/model"
fi

# Check if we have a trained model, copy if available
MODEL_PATH="models/beehive_classifier.pkl"
if [ -f "$MODEL_PATH" ]; then
    echo "Copying trained model to function source"
    cp "$MODEL_PATH" "$SOURCE_DIR/model/"
else
    echo "Warning: No trained model found at $MODEL_PATH"
    echo "The function will use rule-based classification."
fi

# Deploy the function
echo "Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
    --project $PROJECT_ID \
    --region $REGION \
    --runtime $RUNTIME \
    --trigger-resource $BUCKET_NAME \
    --trigger-event google.storage.object.finalize \
    --source $SOURCE_DIR \
    --entry-point $ENTRY_POINT \
    --memory $MEMORY \
    --timeout $TIMEOUT \
    --retry

echo
echo "========== Deployment Summary =========="
echo "Cloud Function $FUNCTION_NAME has been deployed."
echo "It will be triggered when files are uploaded to gs://$BUCKET_NAME"
echo
echo "To test the function, run:"
echo "./scripts/simulate_iot_uploads.py --bucket $BUCKET_NAME --count 5 --simulate-events"
echo "=======================================" 