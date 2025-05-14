#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
BUCKET_NAME="beehive-audio-bucket"
MODEL_NAME="beehive-classifier"

# Create GCS bucket
echo "Creating GCS bucket..."
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME

# Deploy Cloud Function
echo "Deploying Cloud Function..."
gcloud functions deploy process_audio \
    --project $PROJECT_ID \
    --region $REGION \
    --runtime python310 \
    --trigger-resource $BUCKET_NAME \
    --trigger-event google.storage.object.finalize \
    --source src/cloud \
    --entry-point process_audio \
    --memory 1GB \
    --timeout 60s \
    --set-env-vars "TWILIO_SID=your-twilio-sid,TWILIO_AUTH=your-twilio-auth,TWILIO_FROM=your-twilio-number,ALERT_PHONE_TO=your-phone,SENDGRID_API_KEY=your-sendgrid-key,ALERT_EMAIL_TO=your-email"

# Build and push Docker image
echo "Building and pushing Docker image..."
IMAGE_NAME="gcr.io/$PROJECT_ID/beehive-dashboard"
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy beehive-dashboard \
    --project $PROJECT_ID \
    --region $REGION \
    --image $IMAGE_NAME \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

echo "Deployment complete!"
echo "Dashboard URL: $(gcloud run services describe beehive-dashboard --platform managed --region $REGION --format 'value(status.url)')" 