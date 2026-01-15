"""Model training module."""

import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

from .config import Config
from .preprocessing import load_and_preprocess
from .feature_engineering import create_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Handles model training and persistence."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.model = None
        self.feature_names = []
        
    def split_data(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into train and test sets.
        
        NOTE: For t->t+1 prediction, should use temporal split.
        This is a placeholder using random split.
        
        Args:
            X: Features
            y: Target
            test_size: Proportion of test set
            random_state: Random seed
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        logger.info(f"Splitting data: test_size={test_size}")
        
        # TODO: implement temporal split when year information is available
        # For now, use stratified random split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y
        )
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Class distribution (train): {y_train.value_counts().to_dict()}")
        
        return X_train, X_test, y_train, y_test
    
    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series
    ) -> RandomForestClassifier:
        """
        Train the model.
        
        Args:
            X_train: Training features
            y_train: Training target
            
        Returns:
            Trained model
        """
        logger.info("Training Random Forest model")
        
        # Store feature names
        self.feature_names = X_train.columns.tolist()
        
        # Initialize model
        # NOTE: These hyperparameters are placeholders. Tune in later phases.
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight='balanced',  # Handle class imbalance
            random_state=self.config.RANDOM_STATE,
            n_jobs=-1
        )
        
        # Train
        self.model.fit(X_train, y_train)
        
        logger.info("Training complete")
        
        return self.model
    
    def save_model(
        self,
        output_path: Optional[Path] = None,
        metadata: Optional[dict] = None
    ):
        """
        Save trained model to disk.
        
        Args:
            output_path: Path to save model. If None, use default from config.
            metadata: Optional metadata to save alongside model
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")
        
        if output_path is None:
            output_path = self.config.get_model_path()
        
        logger.info(f"Saving model to {output_path}")
        
        # Save model
        joblib.dump(self.model, output_path)
        
        # Save metadata
        if metadata is not None:
            import json
            metadata_path = output_path.parent / "model_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
        
        # Save feature names
        feature_names_path = output_path.parent / "feature_names.txt"
        with open(feature_names_path, 'w') as f:
            f.write('\n'.join(self.feature_names))
        logger.info(f"Saved feature names to {feature_names_path}")


def train_pipeline(
    data_path: str,
    output_dir: str,
    config: Optional[Config] = None
):
    """
    Run full training pipeline.
    
    Args:
        data_path: Path to input data
        output_dir: Directory to save trained model
        config: Configuration object
    """
    config = config or Config()
    
    logger.info("=" * 80)
    logger.info("STARTING TRAINING PIPELINE")
    logger.info("=" * 80)
    
    # 1. Load and preprocess data
    logger.info("Step 1: Loading and preprocessing data")
    df, preprocessor = load_and_preprocess(data_path, config)
    
    # 2. Feature engineering
    logger.info("Step 2: Feature engineering")
    df_features, engineer = create_features(df, config)
    
    # 3. Split features and target
    logger.info("Step 3: Splitting features and target")
    
    if config.TARGET_COLUMN not in df_features.columns:
        raise ValueError(f"Target column '{config.TARGET_COLUMN}' not found in data")
    
    y = df_features[config.TARGET_COLUMN]
    X = df_features.drop(columns=[config.TARGET_COLUMN])
    
    logger.info(f"Features shape: {X.shape}")
    logger.info(f"Target distribution: {y.value_counts().to_dict()}")
    
    # 4. Train model
    logger.info("Step 4: Training model")
    trainer = ModelTrainer(config)
    
    X_train, X_test, y_train, y_test = trainer.split_data(X, y)
    model = trainer.train_model(X_train, y_train)
    
    # 5. Quick evaluation (detailed evaluation in evaluate.py)
    from sklearn.metrics import classification_report, recall_score
    
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    recall_train = recall_score(y_train, y_pred_train, pos_label=1)
    recall_test = recall_score(y_test, y_pred_test, pos_label=1)
    
    logger.info(f"Recall (train): {recall_train:.3f}")
    logger.info(f"Recall (test): {recall_test:.3f}")
    logger.info("\nClassification Report (test):")
    logger.info("\n" + classification_report(y_test, y_pred_test))
    
    # 6. Save model
    logger.info("Step 5: Saving model")
    output_path = Path(output_dir) / "model.pkl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "version": "v0.1.0",
        "model_type": "RandomForestClassifier",
        "n_features": X_train.shape[1],
        "feature_names": X_train.columns.tolist(),
        "target": config.TARGET_COLUMN,
        "recall_train": float(recall_train),
        "recall_test": float(recall_test),
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    trainer.save_model(output_path, metadata)
    
    logger.info("=" * 80)
    logger.info("TRAINING PIPELINE COMPLETE")
    logger.info("=" * 80)


def main():
    """CLI entry point for training."""
    parser = argparse.ArgumentParser(description="Train dropout risk prediction model")
    parser.add_argument(
        "--data",
        type=str,
        default="data/raw/dataset_2022_2024.csv",
        help="Path to input data CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/",
        help="Output directory for trained model"
    )
    
    args = parser.parse_args()
    
    # Check if data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        logger.info("This is a placeholder training script.")
        logger.info("Place your data at: data/raw/dataset_2022_2024.csv")
        logger.info("Or specify path with --data argument")
        return
    
    # Run training pipeline
    try:
        train_pipeline(str(data_path), args.output)
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
