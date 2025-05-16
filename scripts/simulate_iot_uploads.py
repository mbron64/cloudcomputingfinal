#!/usr/bin/env python3
"""
Simulate IoT device uploads to cloud storage or local files.
This script generates simulated beehive audio data and uploads it to either:
1. Local simulation_output directory (default)
2. Google Cloud Storage bucket (when --cloud flag is used)
"""

import os
import json
import time
import random
import argparse
import datetime
import numpy as np
from pathlib import Path

# Try to import Google Cloud Storage, but don't fail if not available
try:
    from google.cloud import storage
    HAVE_STORAGE = True
except ImportError:
    HAVE_STORAGE = False

# Constants
NUM_DEVICES = 3
BEHAVIORS = ["normal", "swarming", "distress"]
BEHAVIOR_PROBABILITIES = {
    "normal": 0.8,
    "swarming": 0.15,
    "distress": 0.05,
}

def generate_device_id():
    """Generate a random device ID in format HIVE-XXXX"""
    return f"HIVE-{random.randint(1000, 9999)}"

def generate_audio_features():
    """Generate random audio features that mimic real beehive sounds"""
    # Base values typical for beehive sounds
    features = {
        "audio_density": random.uniform(0.4, 0.8),
        "frequency_mean": random.uniform(200, 600),
        "frequency_std": random.uniform(50, 150),
        "amplitude_mean": random.uniform(0.3, 0.7),
        "amplitude_std": random.uniform(0.05, 0.2),
        "zero_crossing_rate": random.uniform(0.1, 0.4),
        "spectral_centroid": random.uniform(300, 700),
        "spectral_bandwidth": random.uniform(200, 500),
        "spectral_rolloff": random.uniform(0.7, 0.95),
        "spectral_contrast": random.uniform(0.2, 0.8),
        "tempo_bpm": random.uniform(80, 140),
        "harmonic_ratio": random.uniform(0.3, 0.8),
        "pitch_mean": random.uniform(150, 450),
        "pitch_std": random.uniform(20, 80),
        "mfcc1": random.uniform(-20, 20),
        "mfcc2": random.uniform(-15, 15),
        "mfcc3": random.uniform(-10, 10),
        "energy_variation": random.uniform(0.05, 0.3),
        "density_variation": random.uniform(0.1, 0.5),
    }
    
    return features

def modify_features_by_behavior(features, behavior):
    """Modify features based on bee behavior"""
    if behavior == "normal":
        return features
    
    # Create a copy to avoid modifying the original
    modified = features.copy()
    
    if behavior == "swarming":
        # Swarming has higher density, amplitude, and energy variation
        modified["audio_density"] *= random.uniform(1.2, 1.5)
        modified["amplitude_mean"] *= random.uniform(1.1, 1.3)
        modified["tempo_bpm"] *= random.uniform(1.2, 1.4)
        modified["energy_variation"] *= random.uniform(1.5, 2.0)
        modified["density_variation"] *= random.uniform(1.3, 1.8)
    
    elif behavior == "distress":
        # Distress has higher pitch, frequency and spectral values
        modified["frequency_mean"] *= random.uniform(1.3, 1.6)
        modified["frequency_std"] *= random.uniform(1.4, 1.8)
        modified["pitch_mean"] *= random.uniform(1.2, 1.5)
        modified["spectral_centroid"] *= random.uniform(1.3, 1.6)
        modified["zero_crossing_rate"] *= random.uniform(1.4, 1.8)
    
    return modified

def generate_sample(device_id, timestamp=None):
    """Generate a complete sample with metadata and features"""
    if timestamp is None:
        timestamp = datetime.datetime.now().isoformat()
    
    # Choose a behavior based on probabilities
    behavior = random.choices(
        BEHAVIORS, 
        weights=[BEHAVIOR_PROBABILITIES[b] for b in BEHAVIORS]
    )[0]
    
    # Generate base features and modify for behavior
    base_features = generate_audio_features()
    features = modify_features_by_behavior(base_features, behavior)
    
    # Create sample object
    sample = {
        "device_id": device_id,
        "timestamp": timestamp,
        "battery_level": random.uniform(0.3, 1.0),
        "temperature": random.uniform(20, 40),
        "humidity": random.uniform(0.3, 0.9),
        "audio_features": features,
        # In a real system, we'd have the ground truth from annotations
        # Here we're simulating it for demo purposes
        "true_behavior": behavior  
    }
    
    return sample

def save_local(sample, output_dir="simulation_output"):
    """Save a sample to a local JSON file"""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate filename based on timestamp and device ID
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{output_dir}/{sample['device_id']}_{timestamp}.json"
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(sample, f, indent=2)
    
    return filename

def upload_to_gcs(sample, bucket_name):
    """Upload a sample to Google Cloud Storage"""
    if not HAVE_STORAGE:
        print("WARNING: google-cloud-storage is not installed. Install with 'pip install google-cloud-storage'")
        return None
        
    # Create a GCS client
    client = storage.Client()
    
    # Get the bucket
    bucket = client.bucket(bucket_name)
    
    # Generate a filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    blob_name = f"beehive_data/{sample['device_id']}_{timestamp}.json"
    
    # Create a new blob and upload the file
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(sample, indent=2),
        content_type='application/json'
    )
    
    return blob_name

def run_simulation(args):
    """Run the simulation based on command-line arguments"""
    print(f"Starting beehive IoT simulation with {args.devices} devices")
    
    # Generate device IDs
    device_ids = [generate_device_id() for _ in range(args.devices)]
    
    # Report configuration
    print(f"Device IDs: {', '.join(device_ids)}")
    if args.cloud:
        print(f"Uploading to GCS bucket: {args.bucket}")
    else:
        print(f"Saving to local directory: {args.output_dir}")
    
    # Run for specified duration or number of samples
    start_time = time.time()
    sample_count = 0
    
    try:
        while True:
            # Check if we've hit the sample limit
            if args.samples and sample_count >= args.samples:
                break
            
            # Check if we've hit the time limit
            if args.duration and (time.time() - start_time) >= args.duration:
                break
            
            # Generate a sample for each device
            for device_id in device_ids:
                # Generate a sample
                sample = generate_sample(device_id)
                
                # Save or upload the sample
                if args.cloud:
                    filepath = upload_to_gcs(sample, args.bucket)
                    location = f"gs://{args.bucket}/{filepath}"
                else:
                    filepath = save_local(sample, args.output_dir)
                    location = filepath
                
                print(f"Generated sample for device {device_id}: {sample['true_behavior']} -> {location}")
                sample_count += 1
            
            # Wait before generating the next batch
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    
    print(f"Simulation complete. Generated {sample_count} samples.")

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Simulate beehive IoT device uploads")
    
    # Simulation parameters
    parser.add_argument("--devices", type=int, default=3,
                        help="Number of IoT devices to simulate")
    parser.add_argument("--samples", type=int, default=10,
                        help="Number of samples to generate (0 for unlimited)")
    parser.add_argument("--duration", type=int, default=0,
                        help="Duration in seconds to run simulation (0 for unlimited)")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Interval in seconds between sample batches")
    
    # Output options
    parser.add_argument("--cloud", action="store_true",
                        help="Upload to Google Cloud Storage instead of local files")
    parser.add_argument("--bucket", type=str, default="",
                        help="GCS bucket name for uploads (required with --cloud)")
    parser.add_argument("--output-dir", type=str, default="simulation_output",
                        help="Directory for local output files")
    
    args = parser.parse_args()
    
    # Validate args
    if args.cloud:
        if not HAVE_STORAGE:
            parser.error("--cloud requires google-cloud-storage to be installed. Run 'pip install google-cloud-storage'")
        if not args.bucket:
            parser.error("--cloud requires --bucket to be specified")
    
    return args

if __name__ == "__main__":
    args = parse_args()
    run_simulation(args) 