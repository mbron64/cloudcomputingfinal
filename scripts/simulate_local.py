#!/usr/bin/env python3
"""
Simulates IoT device uploads locally without requiring GCP credentials.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import joblib

# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.data.data_loader import MSPBDataLoader

# Labels for classification
LABELS = ["normal", "swarming", "distress"]

def create_audio_json(features: pd.Series, hive_id: str = "hive001") -> dict:
    """
    Create a JSON representation of audio data.
    
    Args:
        features: Series containing audio features
        hive_id: Hive identifier
        
    Returns:
        Dictionary with formatted audio data
    """
    # Extract audio features (frequencies)
    hz_values = {}
    for col in features.index:
        if col.startswith("hz_"):
            freq = col.replace("hz_", "")
            hz_values[freq] = float(features[col])
    
    # Create a JSON payload similar to what an IoT device would send
    return {
        "device_id": hive_id,
        "timestamp": datetime.now().isoformat(),
        "audio": {
            "frequencies": hz_values,
            "audio_density": float(features.get("audio_density", 0)),
            "audio_density_ratio": float(features.get("audio_density_ratio", 0)),
            "density_variation": float(features.get("density_variation", 0))
        },
        "metadata": {
            "sample_rate": 48000,
            "duration": 10.0,
            "format": "simulation"
        }
    }

def enhance_audio_features(features: pd.Series, event_type: str) -> pd.Series:
    """
    Enhance audio features to simulate specific events.
    
    Args:
        features: Original audio features
        event_type: Type of event to simulate ('swarming', 'distress', or 'normal')
        
    Returns:
        Modified audio features
    """
    enhanced = features.copy()
    
    # Apply modifications based on event type
    if event_type == 'swarming':
        # Increase mid to high frequencies, increase density
        for col in enhanced.index:
            if col.startswith('hz_') and float(col.replace('hz_', '')) > 300:
                enhanced[col] = enhanced[col] * 1.5  # Amplify higher frequencies
        
        enhanced['audio_density'] = enhanced.get('audio_density', 0) * 2.0
        enhanced['density_variation'] = enhanced.get('density_variation', 0) * 3.0
        
    elif event_type == 'distress':
        # Increase low frequencies, create more variation
        for col in enhanced.index:
            if col.startswith('hz_') and float(col.replace('hz_', '')) < 300:
                enhanced[col] = enhanced[col] * 2.0  # Amplify lower frequencies
        
        enhanced['density_variation'] = enhanced.get('density_variation', 0) * 4.0
        
    return enhanced

def prepare_feature_vector(frequencies: dict, density_metrics: dict) -> np.ndarray:
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

def predict_behavior(feature_vector: np.ndarray, model=None) -> dict:
    """
    Predict bee behavior from feature vector.
    
    Args:
        feature_vector: Feature vector of audio features
        model: Trained classifier (if None, use rule-based approach)
        
    Returns:
        Dictionary with prediction results
    """
    if model is None:
        # If no model is available, use a rule-based approach
        # This is a simplified heuristic
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

def main():
    print("Simulating IoT beehive monitoring system locally...")
    
    # Load model if available
    model_path = Path('models/beehive_classifier.pkl')
    model = None
    if model_path.exists():
        print(f"Loading model from {model_path}")
        model = joblib.load(model_path)
    else:
        print("No model found, will use rule-based prediction")
    
    # Load data
    loader = MSPBDataLoader('data')
    device_id = loader.get_available_devices()[0]
    print(f"Using data from device: {device_id}")
    
    # Load a sample of the data
    data = loader.load_sensor_data(device_id=device_id, nrows=1000)
    audio_features = loader.extract_audio_features(data)
    
    # Create output directory for simulated data
    output_dir = Path('simulation_output')
    output_dir.mkdir(exist_ok=True)
    
    # Simulate 5 events (3 normal, 1 swarming, 1 distress)
    event_types = ["normal", "normal", "normal", "swarming", "distress"]
    
    print(f"\nSimulating {len(event_types)} events:")
    
    for i, event_type in enumerate(event_types):
        print(f"\nEvent {i+1}: {event_type.upper()}")
        
        # Sample a random data point
        sample_idx = np.random.randint(0, len(audio_features))
        sample = audio_features.iloc[sample_idx]
        
        # Enhance features based on event type
        if event_type != "normal":
            print(f"Enhancing features to simulate {event_type} behavior")
            sample = enhance_audio_features(sample, event_type)
        
        # Create the JSON payload
        hive_id = f"hive{np.random.randint(1, 10):03d}"
        timestamp = datetime.now() + timedelta(minutes=i)
        payload = create_audio_json(sample, hive_id)
        payload["timestamp"] = timestamp.isoformat()  # Use sequential timestamps
        
        # Save JSON to file
        filename = f"{hive_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{event_type}.json"
        json_path = output_dir / filename
        with open(json_path, 'w') as f:
            json.dump(payload, f, indent=2)
            
        print(f"Saved payload to {json_path}")
        
        # Extract features from payload
        audio_data = payload["audio"]
        frequencies = audio_data["frequencies"]
        density_metrics = {
            'audio_density': audio_data['audio_density'],
            'audio_density_ratio': audio_data['audio_density_ratio'],
            'density_variation': audio_data['density_variation']
        }
        
        # Prepare feature vector
        feature_vector = prepare_feature_vector(frequencies, density_metrics)
        
        # Predict behavior
        result = predict_behavior(feature_vector, model)
        
        # Print prediction
        print(f"Prediction: {result['prediction'].upper()} (confidence: {result['confidence']:.2f})")
        print(f"Probabilities: {', '.join([f'{k}: {v:.2f}' for k, v in result['probabilities'].items()])}")
        
        # Alert if high-risk behavior is detected
        if result['prediction'] in ['swarming', 'distress'] and result['confidence'] > 0.6:
            print(f"🚨 ALERT: {result['prediction'].upper()} behavior detected with confidence {result['confidence']:.2f}!")
    
    print("\nSimulation complete! Results saved to the simulation_output directory.")

if __name__ == "__main__":
    main() 