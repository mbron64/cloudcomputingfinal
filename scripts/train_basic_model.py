#!/usr/bin/env python3
"""
Train a basic classifier on a small subset of the MSPB dataset.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.data.data_loader import MSPBDataLoader

def main():
    print("Training a basic beehive behavior classifier...")
    
    # Load a sample of the data
    loader = MSPBDataLoader('data')
    device_ids = loader.get_available_devices()
    print(f"Available devices: {device_ids}")
    
    device_id = device_ids[0]  # Use the first device
    print(f"Using data from device: {device_id}")
    
    # Load a small subset of the data (1000 samples)
    data = loader.load_sensor_data(device_id=device_id, nrows=1000)
    features_df = loader.extract_audio_features(data)
    
    # Extract features (exclude timestamp)
    feature_columns = [col for col in features_df.columns if col != 'published_at']
    X = features_df[feature_columns].values
    
    # For demonstration purposes, create synthetic labels
    # In a real application, we would map annotations to timestamps
    # 0 = normal, 1 = swarming, 2 = distress
    # Let's create a somewhat realistic distribution: mostly normal, some swarming, few distress
    np.random.seed(42)
    probabilities = [0.8, 0.15, 0.05]  # 80% normal, 15% swarming, 5% distress
    y = np.random.choice([0, 1, 2], size=len(X), p=probabilities)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Label counts: normal={sum(y==0)}, swarming={sum(y==1)}, distress={sum(y==2)}")
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train a Random Forest classifier
    print("\nTraining Random Forest classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = clf.predict(X_test)
    print("\nClassification Report:")
    labels = ['normal', 'swarming', 'distress']
    print(classification_report(y_test, y_pred, target_names=labels))
    
    # Save the model
    model_dir = Path('models')
    model_dir.mkdir(exist_ok=True)
    model_path = model_dir / 'beehive_classifier.pkl'
    joblib.dump(clf, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Generate feature importances
    feature_importances = pd.DataFrame({
        'feature': feature_columns,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 important features:")
    print(feature_importances.head(10))

if __name__ == "__main__":
    main() 