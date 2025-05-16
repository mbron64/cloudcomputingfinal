"""
Data loader module for MSPB dataset in CSV/XLSX format.
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from pathlib import Path


class MSPBDataLoader:
    """Data loader for MSPB dataset provided in CSV/XLSX format."""
    
    def __init__(self, data_dir: str = 'data'):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Directory containing MSPB dataset files
        """
        self.data_dir = Path(data_dir)
        self.sensor_files = {}
        self.annotation_files = {}
        
        # Find sensor data and annotation files
        for file in self.data_dir.glob('*.csv'):
            if 'sensor_data' in file.name:
                device_id = file.name.split('_')[0]
                self.sensor_files[device_id] = file
                
        for file in self.data_dir.glob('*.xlsx'):
            if 'ant' in file.name:
                device_id = file.name.split('_')[0]
                self.annotation_files[device_id] = file
    
    def load_sensor_data(self, device_id: str = None, nrows: int = None) -> pd.DataFrame:
        """
        Load sensor data for a specific device.
        
        Args:
            device_id: Device ID to load (e.g., 'D1', 'D2')
            nrows: Number of rows to load (None for all)
            
        Returns:
            DataFrame of sensor data
        """
        if device_id is not None:
            if device_id not in self.sensor_files:
                raise ValueError(f"No sensor data found for device {device_id}")
            file_path = self.sensor_files[device_id]
        else:
            # Load the first file if no device_id is specified
            if not self.sensor_files:
                raise ValueError("No sensor data files found")
            device_id = next(iter(self.sensor_files))
            file_path = self.sensor_files[device_id]
        
        print(f"Loading sensor data from {file_path}")
        return pd.read_csv(file_path, nrows=nrows)
    
    def load_annotations(self, device_id: str = None) -> pd.DataFrame:
        """
        Load annotations for a specific device.
        
        Args:
            device_id: Device ID to load (e.g., 'D1', 'D2')
            
        Returns:
            DataFrame of annotations
        """
        if device_id is not None:
            if device_id not in self.annotation_files:
                raise ValueError(f"No annotations found for device {device_id}")
            file_path = self.annotation_files[device_id]
        else:
            # Load the first file if no device_id is specified
            if not self.annotation_files:
                raise ValueError("No annotation files found")
            device_id = next(iter(self.annotation_files))
            file_path = self.annotation_files[device_id]
        
        print(f"Loading annotations from {file_path}")
        return pd.read_excel(file_path)
    
    def extract_audio_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract audio features from sensor data.
        
        Args:
            data: DataFrame of sensor data
            
        Returns:
            DataFrame with audio features
        """
        # Find all audio-related columns
        audio_columns = [col for col in data.columns if col.startswith('hz_') or 
                         col in ['audio_density', 'audio_density_ratio', 'density_variation']]
        
        # Select relevant columns
        features = data[['published_at'] + audio_columns].copy()
        
        return features
    
    def create_classification_dataset(self, 
                                      device_id: str = None,
                                      feature_columns: List[str] = None,
                                      target_column: str = None,
                                      sample_frac: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create a classification dataset from sensor data and annotations.
        
        Args:
            device_id: Device ID to use
            feature_columns: Columns to use as features
            target_column: Column to use as target
            sample_frac: Fraction of data to sample
            
        Returns:
            Tuple of (X, y) arrays for model training
        """
        # Load sensor data and annotations
        sensor_data = self.load_sensor_data(device_id)
        annotations = self.load_annotations(device_id)
        
        # For demonstration, we'll create a placeholder dataset
        # In a real implementation, you would match sensor data with annotations
        # and extract relevant features and labels
        
        # Sample data
        if sample_frac < 1.0:
            sensor_data = sensor_data.sample(frac=sample_frac, random_state=42)
        
        # Extract audio features if no specific columns are provided
        if feature_columns is None:
            features_df = self.extract_audio_features(sensor_data)
            feature_columns = [col for col in features_df.columns if col != 'published_at']
        else:
            features_df = sensor_data[feature_columns + ['published_at']]
        
        # Create features array
        X = features_df[feature_columns].values
        
        # For demonstration, create a synthetic target
        # In a real implementation, you would map annotations to sensor data timestamps
        # and extract the actual target values
        if target_column is None:
            # Synthetic labels: 0 = normal, 1 = swarming, 2 = distress
            # Here we're just randomly assigning labels
            y = np.random.randint(0, 3, size=X.shape[0])
        else:
            y = annotations[target_column].values
            
        return X, y
    
    def get_available_devices(self) -> List[str]:
        """
        Get list of available device IDs.
        
        Returns:
            List of device IDs
        """
        return list(self.sensor_files.keys())


if __name__ == "__main__":
    # Example usage
    loader = MSPBDataLoader('data')
    print("Available devices:", loader.get_available_devices())
    
    # Load a sample of sensor data
    sample_data = loader.load_sensor_data(nrows=5)
    print("\nSensor data sample:")
    print(sample_data.head())
    
    # Extract audio features
    audio_features = loader.extract_audio_features(sample_data)
    print("\nAudio features sample:")
    print(audio_features.head())
    
    # Create a classification dataset
    X, y = loader.create_classification_dataset(sample_frac=0.01)
    print(f"\nClassification dataset created with {X.shape[0]} samples")
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}") 