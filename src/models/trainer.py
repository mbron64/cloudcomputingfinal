"""
Model training module for beehive behavior classification.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class BeehiveBehaviorTrainer:
    """Trainer for beehive behavior classification model."""
    
    def __init__(
        self,
        model_dir: str = 'models',
        random_state: int = 42
    ):
        """
        Initialize the trainer.
        
        Args:
            model_dir: Directory to save trained models
            random_state: Random seed for reproducibility
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.random_state = random_state
        self.model = None
        self.label_mapping = None
        
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs
    ) -> RandomForestClassifier:
        """
        Train a Random Forest classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            **kwargs: Additional arguments for RandomForestClassifier
            
        Returns:
            Trained RandomForestClassifier
        """
        # Initialize model with default or provided parameters
        model_params = {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': self.random_state,
            **kwargs
        }
        
        self.model = RandomForestClassifier(**model_params)
        self.model.fit(X_train, y_train)
        
        return self.model
    
    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        label_names: Dict[int, str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the trained model.
        
        Args:
            X_test: Test features
            y_test: Test labels
            label_names: Mapping from label indices to names
            
        Returns:
            Dictionary containing evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")
            
        # Get predictions
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        report = classification_report(
            y_test,
            y_pred,
            target_names=label_names.values() if label_names else None,
            output_dict=True
        )
        
        # Create confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Plot confusion matrix
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=label_names.values() if label_names else None,
            yticklabels=label_names.values() if label_names else None
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        # Save plot
        plt.savefig(self.model_dir / 'confusion_matrix.png')
        plt.close()
        
        return {
            'classification_report': report,
            'confusion_matrix': cm
        }
    
    def save_model(self, model_name: str = 'beehive_classifier'):
        """
        Save the trained model and metadata.
        
        Args:
            model_name: Base name for saved files
        """
        if self.model is None:
            raise ValueError("No model to save")
            
        # Save model
        model_path = self.model_dir / f'{model_name}.pkl'
        joblib.dump(self.model, model_path)
        
        # Save feature importances
        importances = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(len(self.model.feature_importances_))],
            'importance': self.model.feature_importances_
        })
        importances.to_csv(self.model_dir / f'{model_name}_importances.csv', index=False)
        
        # Plot feature importances
        plt.figure(figsize=(10, 6))
        sns.barplot(data=importances, x='importance', y='feature')
        plt.title('Feature Importances')
        plt.tight_layout()
        plt.savefig(self.model_dir / 'feature_importances.png')
        plt.close()
        
    def load_model(self, model_path: str) -> RandomForestClassifier:
        """
        Load a trained model.
        
        Args:
            model_path: Path to saved model file
            
        Returns:
            Loaded RandomForestClassifier
        """
        self.model = joblib.load(model_path)
        return self.model

def main():
    """Main training script."""
    import argparse
    from ..data.preprocessor import MSPBPreprocessor
    
    parser = argparse.ArgumentParser(description='Train beehive behavior classifier')
    parser.add_argument('--data_dir', required=True, help='Directory containing MSPB dataset')
    parser.add_argument('--output_dir', default='processed_data', help='Directory for processed data')
    parser.add_argument('--model_dir', default='models', help='Directory for saved models')
    args = parser.parse_args()
    
    # Preprocess data
    preprocessor = MSPBPreprocessor(args.data_dir)
    X_train, X_test, y_train, y_test = preprocessor.prepare_dataset()
    
    # Save processed data
    preprocessor.save_processed_data(args.output_dir, X_train, X_test, y_train, y_test)
    
    # Train model
    trainer = BeehiveBehaviorTrainer(model_dir=args.model_dir)
    model = trainer.train(X_train, y_train)
    
    # Evaluate model
    label_names = {i: label for i, label in enumerate(preprocessor.label_mapping.values())}
    metrics = trainer.evaluate(X_test, y_test, label_names)
    
    # Print results
    print("\nClassification Report:")
    print(pd.DataFrame(metrics['classification_report']).T)
    
    # Save model
    trainer.save_model()

if __name__ == '__main__':
    main()
