"""
Cloud Function for processing beehive audio files.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
import numpy as np
from google.cloud import storage, firestore
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import joblib

# Load model at cold start
MODEL_PATH = os.path.join(os.getenv('FUNCTION_SOURCE', ''), 'models/beehive_classifier.pkl')
model = joblib.load(MODEL_PATH)

# Initialize clients
storage_client = storage.Client()
firestore_client = firestore.Client()

# Get alert configuration
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH = os.getenv('TWILIO_AUTH')
TWILIO_FROM = os.getenv('TWILIO_FROM')
ALERT_PHONE_TO = os.getenv('ALERT_PHONE_TO')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO')

def process_audio(event: Dict[str, Any], context: Any) -> None:
    """
    Cloud Function triggered by a new file in GCS bucket.
    
    Args:
        event: Cloud Storage event
        context: Cloud Function context
    """
    # Get bucket and file info
    bucket_name = event['bucket']
    file_name = event['name']
    
    # Skip if not an audio file
    if not file_name.lower().endswith(('.wav', '.mp3')):
        print(f"Skipping non-audio file: {file_name}")
        return
    
    print(f"Processing audio file: {file_name}")
    
    # Download file to temporary location
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    temp_dir = tempfile.mkdtemp()
    local_path = os.path.join(temp_dir, file_name)
    blob.download_to_filename(local_path)
    
    try:
        # Extract features and predict
        from ..utils.audio_utils import process_audio_file
        feature_vector, metadata = process_audio_file(local_path)
        prediction = model.predict([feature_vector])[0]
        probabilities = model.predict_proba([feature_vector])[0]
        
        # Get prediction label
        label_names = ['normal', 'swarming', 'distress']  # Update based on your model
        prediction_label = label_names[prediction]
        
        # Store result in Firestore
        doc_ref = firestore_client.collection('hive_classifications').document(file_name)
        doc_ref.set({
            'audio_file': file_name,
            'prediction': prediction_label,
            'probabilities': probabilities.tolist(),
            'metadata': metadata,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # Send alerts if needed
        if prediction_label in ['swarming', 'distress']:
            send_alerts(prediction_label, file_name, probabilities)
            
    finally:
        # Clean up temporary file
        os.remove(local_path)
        os.rmdir(temp_dir)

def send_alerts(
    prediction: str,
    file_name: str,
    probabilities: np.ndarray
) -> None:
    """
    Send alerts via SMS and email for critical events.
    
    Args:
        prediction: Predicted behavior category
        file_name: Name of the audio file
        probabilities: Prediction probabilities
    """
    # Prepare alert message
    message = (
        f"🚨 Beehive Alert!\n"
        f"Detected {prediction.upper()} behavior in {file_name}\n"
        f"Confidence: {probabilities.max():.2%}"
    )
    
    # Send SMS via Twilio
    if all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM, ALERT_PHONE_TO]):
        try:
            client = TwilioClient(TWILIO_SID, TWILIO_AUTH)
            message = client.messages.create(
                body=message,
                from_=TWILIO_FROM,
                to=ALERT_PHONE_TO
            )
            print(f"Sent SMS alert: {message.sid}")
        except Exception as e:
            print(f"Failed to send SMS: {e}")
    
    # Send email via SendGrid
    if all([SENDGRID_API_KEY, ALERT_EMAIL_TO]):
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            email = Mail(
                from_email='alerts@beehive-monitor.com',
                to_emails=ALERT_EMAIL_TO,
                subject=f'Beehive Alert: {prediction.upper()} Detected',
                plain_text_content=message
            )
            response = sg.send(email)
            print(f"Sent email alert: {response.status_code}")
        except Exception as e:
            print(f"Failed to send email: {e}") 