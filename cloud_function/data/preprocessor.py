"""
Data preprocessing module for the MSPB dataset.
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from pathlib import Path
from ..utils.audio_utils import process_audio_file

class MSPBPreprocessor:
    """Preprocessor for the MSPB dataset."""
    
    def __init__(
        self,
        data_dir: str,
        label_mapping: Dict[str, str] = None
    ):
        """
        Initialize the preprocessor.
        
        Args:
            data_dir: Directory containing MSPB dataset
            label_mapping: Optional mapping from raw labels to behavior categories
        """
        self.data_dir = Path(data_dir)
        self.label_mapping = label_mapping or {
            'queenright': 'normal',
            'queenless': 'distress',
            'swarming': 'swarming'
        }
        
    def load_audio_files(self) -> List[str]:
        """
        Find all audio files in the dataset directory.
        
        Returns:
            List of paths to audio files
        """
        audio_files = []
        for ext in ['.wav', '.mp3']:
            audio_files.extend(list(self.data_dir.rglob(f'*{ext}')))
        return [str(f) for f in audio_files]
    
    def get_labels(self, audio_files: List[str]) -> List[str]:
        """
        Extract labels for audio files based on directory structure or metadata.
        
        Args:
            audio_files: List of audio file paths
            
        Returns:
            List of corresponding labels
        """
        labels = []
        for file_path in audio_files:
            # Extract label from directory structure
            # This is a placeholder - adjust based on actual MSPB dataset structure
            parent_dir = Path(file_path).parent.name
            label = self.label_mapping.get(parent_dir, 'normal')
            labels.append(label)
        return labels
    
    def prepare_dataset(
        self,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare the dataset for training.
        
        Args:
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        # Get audio files and labels
        audio_files = self.load_audio_files()
        labels = self.get_labels(audio_files)
        
        # Process audio files to get features
        X = []
        for audio_file in audio_files:
            feature_vector, _ = process_audio_file(audio_file)
            X.append(feature_vector)
        X = np.array(X)
        
        # Convert labels to numerical values
        unique_labels = sorted(set(labels))
        label_to_idx = {label: i for i, label in enumerate(unique_labels)}
        y = np.array([label_to_idx[label] for label in labels])
        
        # Split into train and test sets
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y
        )
        
        return X_train, X_test, y_train, y_test
    
    def save_processed_data(
        self,
        output_dir: str,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray
    ):
        """
        Save processed data to disk.
        
        Args:
            output_dir: Directory to save processed data
            X_train: Training features
            X_test: Test features
            y_train: Training labels
            y_test: Test labels
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        np.save(output_dir / 'X_train.npy', X_train)
        np.save(output_dir / 'X_test.npy', X_test)
        np.save(output_dir / 'y_train.npy', y_train)
        np.save(output_dir / 'y_test.npy', y_test)
        
        # Save label mapping
        label_mapping_df = pd.DataFrame({
            'label': list(self.label_mapping.keys()),
            'category': list(self.label_mapping.values())
        })
        label_mapping_df.to_csv(output_dir / 'label_mapping.csv', index=False)
