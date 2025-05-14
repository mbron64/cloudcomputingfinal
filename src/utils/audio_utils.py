"""
Audio processing utilities for beehive monitoring.
"""

import numpy as np
import librosa
from typing import Tuple, Dict, Any

def extract_audio_features(
    audio_path: str,
    sr: int = None,
    n_mfcc: int = 13
) -> Dict[str, np.ndarray]:
    """
    Extract audio features from a beehive audio recording.
    
    Args:
        audio_path: Path to the audio file
        sr: Sampling rate (None to use original)
        n_mfcc: Number of MFCC coefficients to extract
        
    Returns:
        Dictionary containing extracted features:
        - mfccs: Mel-frequency cepstral coefficients
        - spectral_centroid: Spectral centroid
        - zero_crossing_rate: Zero crossing rate
    """
    # Load audio file
    y, sr = librosa.load(audio_path, sr=sr)
    
    # Extract MFCCs
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # Extract spectral centroid
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    
    # Extract zero crossing rate
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
    
    # Aggregate features (take mean across time)
    features = {
        'mfccs': np.mean(mfccs, axis=1),
        'spectral_centroid': np.mean(spectral_centroid),
        'zero_crossing_rate': np.mean(zero_crossing_rate)
    }
    
    return features

def get_feature_vector(features: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Convert feature dictionary to a single feature vector.
    
    Args:
        features: Dictionary of features from extract_audio_features
        
    Returns:
        Concatenated feature vector
    """
    return np.concatenate([
        features['mfccs'],
        [features['spectral_centroid']],
        [features['zero_crossing_rate']]
    ])

def process_audio_file(
    audio_path: str,
    sr: int = None,
    n_mfcc: int = 13
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Process an audio file and return both feature vector and metadata.
    
    Args:
        audio_path: Path to the audio file
        sr: Sampling rate (None to use original)
        n_mfcc: Number of MFCC coefficients to extract
        
    Returns:
        Tuple of (feature_vector, metadata)
    """
    # Extract features
    features = extract_audio_features(audio_path, sr=sr, n_mfcc=n_mfcc)
    
    # Get feature vector
    feature_vector = get_feature_vector(features)
    
    # Get audio metadata
    y, sr = librosa.load(audio_path, sr=sr)
    duration = librosa.get_duration(y=y, sr=sr)
    
    metadata = {
        'duration': duration,
        'sampling_rate': sr,
        'n_samples': len(y)
    }
    
    return feature_vector, metadata
