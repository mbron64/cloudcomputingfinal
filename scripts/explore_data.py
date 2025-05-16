#!/usr/bin/env python3
"""
Script to explore and analyze the MSPB dataset.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.data.data_loader import MSPBDataLoader

def plot_audio_features(data: pd.DataFrame, device_id: str, n_samples: int = 1000):
    """
    Plot audio features over time.
    
    Args:
        data: DataFrame containing audio features
        device_id: Device ID for the plot title
        n_samples: Number of samples to plot
    """
    # Ensure we're only plotting a subset of the data
    if len(data) > n_samples:
        data = data.sample(n_samples, random_state=42)
    
    # Convert published_at to datetime if needed
    if not pd.api.types.is_datetime64_dtype(data['published_at']):
        data['published_at'] = pd.to_datetime(data['published_at'])
    
    # Sort by time
    data = data.sort_values('published_at')
    
    # Filter just the frequency columns for plotting
    hz_cols = [col for col in data.columns if col.startswith('hz_')]
    
    # Create a long-format DataFrame for seaborn
    plot_data = pd.melt(
        data,
        id_vars=['published_at'],
        value_vars=hz_cols,
        var_name='Frequency',
        value_name='Amplitude'
    )
    
    # Plot frequency spectrum over time
    plt.figure(figsize=(15, 8))
    sns.lineplot(data=plot_data, x='published_at', y='Amplitude', hue='Frequency', alpha=0.7)
    
    plt.title(f'Frequency Spectrum Over Time - Device {device_id}')
    plt.xlabel('Time')
    plt.ylabel('Amplitude (dB)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / f'frequency_spectrum_{device_id}.png')
    plt.close()
    
    # Plot audio density metrics
    metrics = ['audio_density', 'audio_density_ratio', 'density_variation']
    metrics_in_data = [m for m in metrics if m in data.columns]
    
    if metrics_in_data:
        plt.figure(figsize=(15, 8))
        for metric in metrics_in_data:
            plt.plot(data['published_at'], data[metric], label=metric)
            
        plt.title(f'Audio Metrics Over Time - Device {device_id}')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_dir / f'audio_metrics_{device_id}.png')
        plt.close()

def analyze_annotations(annotations: pd.DataFrame, device_id: str):
    """
    Analyze and visualize annotation data.
    
    Args:
        annotations: DataFrame of annotations
        device_id: Device ID for the plot title
    """
    print(f"\nAnnotation columns for device {device_id}:")
    print(annotations.columns.tolist())
    
    print(f"\nAnnotation summary for device {device_id}:")
    print(annotations.describe())
    
    # Try to identify potentially useful columns for classification
    # This is just a demonstration - you'll need to adapt based on actual data
    categorical_cols = annotations.select_dtypes(include=['object', 'category']).columns.tolist()
    
    print("\nPotential categorical target columns:")
    for col in categorical_cols:
        value_counts = annotations[col].value_counts()
        if 1 < len(value_counts) < 10:  # Reasonable number of categories
            print(f"  - {col}: {dict(value_counts)}")

def main():
    # Initialize data loader
    data_dir = Path('data')
    loader = MSPBDataLoader(data_dir)
    
    print("Available devices:", loader.get_available_devices())
    
    # Process each device
    for device_id in loader.get_available_devices():
        print(f"\n--- Processing device {device_id} ---")
        
        # Load a sample of sensor data
        try:
            # Load a small sample first to check structure
            sample_data = loader.load_sensor_data(device_id, nrows=5)
            print(f"Sensor data columns ({len(sample_data.columns)}):")
            print(sample_data.columns.tolist())
            
            # Extract audio features
            audio_features = loader.extract_audio_features(sample_data)
            print(f"\nAudio feature columns ({len(audio_features.columns)}):")
            print(audio_features.columns.tolist())
            
            # Load a larger sample for plotting
            plot_sample = loader.load_sensor_data(device_id, nrows=1000)
            audio_features_for_plot = loader.extract_audio_features(plot_sample)
            
            # Generate plots
            plot_audio_features(audio_features_for_plot, device_id)
            print(f"Plots saved to outputs/ directory")
            
        except Exception as e:
            print(f"Error processing sensor data for {device_id}: {e}")
        
        # Load and analyze annotations
        try:
            annotations = loader.load_annotations(device_id)
            analyze_annotations(annotations, device_id)
        except Exception as e:
            print(f"Error processing annotations for {device_id}: {e}")

if __name__ == "__main__":
    main() 