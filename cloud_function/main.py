"""
Cloud Function for processing beehive audio features from simulated IoT devices.
"""

import os
import json
import base64
import tempfile
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import joblib
from google.cloud import storage, firestore
from datetime import datetime

# Load model at cold start (if available)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model/beehive_classifier.pkl")
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"Loaded model from {MODEL_PATH}")
    except Exception as e:
        print(f"Error loading model from {MODEL_PATH}: {e}")

# Initialize clients
storage_client = storage.Client()
firestore_client = firestore.Client()

# Labels for classification
LABELS = ["normal", "swarming", "distress"]

def prepare_feature_vector(frequencies: Dict[str, float], density_metrics: Dict[str, float]) -> np.ndarray:
    """
    Prepare a feature vector from audio frequencies and density metrics.
    
    Args:
        frequencies: Dictionary of frequency values
        density_metrics: Dictionary of audio density metrics
        
    Returns:
        Feature vector for prediction
    """
    # Sort frequencies to ensure consistent order
    sorted_freqs = sorted(frequencies.items(), key=lambda x: float(x[0]))
    
    # Extract frequency values
    freq_values = [value for _, value in sorted_freqs]
    
    # Extract density metrics in a consistent order
    density_values = [
        density_metrics.get('audio_density', 0),
        density_metrics.get('audio_density_ratio', 0),
        density_metrics.get('density_variation', 0)
    ]
    
    # Combine into a single feature vector
    return np.array(freq_values + density_values)

def predict_behavior(feature_vector: np.ndarray) -> Dict[str, Any]:
    """
    Predict bee behavior from feature vector.
    
    Args:
        feature_vector: Feature vector of audio features
        
    Returns:
        Dictionary with prediction results
    """
    if model is None:
        # If no model is available, use a rule-based approach
        # This is a simplified heuristic based on feature characteristics
        high_freqs = feature_vector[len(feature_vector)//2:]
        low_freqs = feature_vector[:len(feature_vector)//2]
        density = feature_vector[-3] if len(feature_vector) > 3 else 0
        variation = feature_vector[-1] if len(feature_vector) > 1 else 0
        
        # Simplified rules
        if variation > 35 or density > 20:
            prediction = 1  # swarming
        elif np.mean(low_freqs) > np.mean(high_freqs) * 1.5:
            prediction = 2  # distress
        else:
            prediction = 0  # normal
            
        # Fake probabilities
        probabilities = np.zeros(3)
        probabilities[prediction] = 0.85  # Primary prediction
        other_indices = [i for i in range(3) if i != prediction]
        probabilities[other_indices] = [0.1, 0.05]  # Distribute remaining probability
    else:
        # Use trained model for prediction
        prediction = model.predict([feature_vector])[0]
        probabilities = model.predict_proba([feature_vector])[0]
    
    # Get prediction label and probability
    label = LABELS[prediction]
    confidence = float(probabilities[prediction])
    
    return {
        "prediction": label,
        "confidence": confidence,
        "probabilities": {LABELS[i]: float(p) for i, p in enumerate(probabilities)}
    }

def process_gcs_event(event: Dict[str, Any], context: Any) -> None:
    """
    Process a GCS event triggered by a new file upload.
    
    Args:
        event: Cloud Storage event
        context: Cloud Function context
    """
    # Get bucket and file info
    bucket_name = event['bucket']
    file_name = event['name']
    
    print(f"Processing file: gs://{bucket_name}/{file_name}")
    
    # Skip if not a JSON file
    if not file_name.lower().endswith('.json'):
        print(f"Skipping non-JSON file: {file_name}")
        return
    
    try:
        # Download the file
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        json_content = blob.download_as_text()
        
        # Parse JSON
        data = json.loads(json_content)
        
        # Extract device ID and timestamp
        device_id = data.get('device_id', 'unknown')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Extract audio features
        audio_data = data.get('audio', {})
        frequencies = audio_data.get('frequencies', {})
        
        density_metrics = {
            'audio_density': audio_data.get('audio_density', 0),
            'audio_density_ratio': audio_data.get('audio_density_ratio', 0),
            'density_variation': audio_data.get('density_variation', 0)
        }
        
        # Prepare feature vector
        feature_vector = prepare_feature_vector(frequencies, density_metrics)
        
        # Predict behavior
        prediction_result = predict_behavior(feature_vector)
        
        # Record result in Firestore
        doc_ref = firestore_client.collection('hive_classifications').document()
        doc_data = {
            'device_id': device_id,
            'timestamp': timestamp,
            'file_name': file_name,
            'prediction': prediction_result['prediction'],
            'confidence': prediction_result['confidence'],
            'probabilities': prediction_result['probabilities'],
            'processed_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(doc_data)
        
        print(f"Prediction: {prediction_result['prediction']} "
              f"(confidence: {prediction_result['confidence']:.2f})")
        print(f"Results saved to Firestore, document ID: {doc_ref.id}")
        
        # If high-risk behavior detected, send an alert
        if prediction_result['prediction'] in ['swarming', 'distress'] and prediction_result['confidence'] > 0.6:
            # In a real implementation, this would send an alert via Pub/Sub, SMS, etc.
            print(f"🚨 ALERT: {prediction_result['prediction'].upper()} detected with "
                  f"confidence {prediction_result['confidence']:.2f}!")
            
            # Publish to Pub/Sub topic (would be implemented in production)
            # publish_alert(device_id, prediction_result)
    
    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        # In production, you might want to log this to Error Reporting
        # or a dedicated logging system


def process_pubsub_message(event: Dict[str, Any], context: Any) -> None:
    """
    Process a Pub/Sub message triggered by a topic publish.
    
    Args:
        event: Pub/Sub message event
        context: Cloud Function context
    """
    # Extract message data (base64-encoded)
    if 'data' not in event:
        print("No data found in Pub/Sub message")
        return
        
    try:
        # Decode the message
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        message_data = json.loads(pubsub_message)
        
        print(f"Received Pub/Sub message: {message_data}")
        
        # Extract features from message
        device_id = message_data.get('device_id', 'unknown')
        timestamp = message_data.get('timestamp', datetime.now().isoformat())
        audio_data = message_data.get('audio', {})
        
        # Process similar to GCS event
        frequencies = audio_data.get('frequencies', {})
        density_metrics = {
            'audio_density': audio_data.get('audio_density', 0),
            'audio_density_ratio': audio_data.get('audio_density_ratio', 0),
            'density_variation': audio_data.get('density_variation', 0)
        }
        
        # Prepare feature vector and predict
        feature_vector = prepare_feature_vector(frequencies, density_metrics)
        prediction_result = predict_behavior(feature_vector)
        
        # Record result in Firestore
        doc_ref = firestore_client.collection('hive_classifications').document()
        doc_data = {
            'device_id': device_id,
            'timestamp': timestamp,
            'message_id': context.event_id,
            'prediction': prediction_result['prediction'],
            'confidence': prediction_result['confidence'],
            'probabilities': prediction_result['probabilities'],
            'processed_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(doc_data)
        
        print(f"Prediction: {prediction_result['prediction']} "
              f"(confidence: {prediction_result['confidence']:.2f})")
        print(f"Results saved to Firestore, document ID: {doc_ref.id}")
        
    except Exception as e:
        print(f"Error processing Pub/Sub message: {e}")


# Main entry point - handles either GCS events or Pub/Sub messages
def process_event(event: Dict[str, Any], context: Any) -> None:
    """
    Main entry point for the Cloud Function.
    Handles either GCS events or Pub/Sub messages.
    
    Args:
        event: Event payload
        context: Event context
    """
    # Determine if this is a GCS or Pub/Sub event
    if 'bucket' in event:
        process_gcs_event(event, context)
    elif 'data' in event:
        process_pubsub_message(event, context)
    else:
        print(f"Unknown event type: {event}") 