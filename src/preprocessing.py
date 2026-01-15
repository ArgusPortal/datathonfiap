"""Data preprocessing module."""

import logging
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from .config import Config

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Handles data cleaning and preprocessing."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.missing_stats = {}
        
    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading data from {filepath}")
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that required columns exist and have correct types.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check for prohibited columns
        prohibited_found = [col for col in self.config.PROHIBITED_COLUMNS if col in df.columns]
        if prohibited_found:
            errors.append(f"Prohibited columns found: {prohibited_found}")
        
        # Check for leakage watchlist columns
        leakage_found = [col for col in self.config.LEAKAGE_WATCHLIST if col in df.columns]
        if leakage_found:
            errors.append(f"Leakage watchlist columns found: {leakage_found}")
        
        # Check target column exists
        if self.config.TARGET_COLUMN not in df.columns:
            errors.append(f"Target column '{self.config.TARGET_COLUMN}' not found")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def check_data_quality(self, df: pd.DataFrame) -> dict:
        """
        Check data quality metrics.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with quality metrics
        """
        quality_report = {
            'n_rows': len(df),
            'n_columns': len(df.columns),
            'missing_by_column': df.isnull().sum().to_dict(),
            'missing_pct_by_column': (df.isnull().sum() / len(df)).to_dict(),
            'duplicates': df.duplicated().sum(),
        }
        
        # Check if target has missing values (should be 0)
        if self.config.TARGET_COLUMN in df.columns:
            target_missing = df[self.config.TARGET_COLUMN].isnull().sum()
            quality_report['target_missing'] = target_missing
            if target_missing > 0:
                logger.warning(f"Target column has {target_missing} missing values!")
        
        return quality_report
    
    def remove_prohibited_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove prohibited columns (IDs, sensitive data).
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with prohibited columns removed
        """
        cols_to_remove = [col for col in self.config.PROHIBITED_COLUMNS if col in df.columns]
        if cols_to_remove:
            logger.info(f"Removing prohibited columns: {cols_to_remove}")
            df = df.drop(columns=cols_to_remove)
        return df
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame,
        strategy: str = "median"
    ) -> pd.DataFrame:
        """
        Handle missing values in features.
        
        Args:
            df: Input DataFrame
            strategy: Imputation strategy ('median', 'mean', 'mode', 'drop')
            
        Returns:
            DataFrame with missing values handled
        """
        logger.info(f"Handling missing values with strategy: {strategy}")
        
        # Store missing stats before imputation
        self.missing_stats = df.isnull().sum().to_dict()
        
        if strategy == "drop":
            # Drop rows with any missing values
            df = df.dropna()
            logger.info(f"Dropped rows with missing values. Remaining: {len(df)}")
            
        elif strategy in ["median", "mean", "mode"]:
            # Impute numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    if strategy == "median":
                        fill_value = df[col].median()
                    elif strategy == "mean":
                        fill_value = df[col].mean()
                    else:  # mode
                        fill_value = df[col].mode()[0] if not df[col].mode().empty else 0
                    
                    df[col].fillna(fill_value, inplace=True)
                    logger.debug(f"Imputed {col} with {strategy}: {fill_value}")
            
            # For categorical columns, use mode
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                if df[col].isnull().sum() > 0:
                    mode_value = df[col].mode()[0] if not df[col].mode().empty else "UNKNOWN"
                    df[col].fillna(mode_value, inplace=True)
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate rows.
        
        Args:
            df: Input DataFrame
            subset: Columns to consider for identifying duplicates
            
        Returns:
            DataFrame with duplicates removed
        """
        n_before = len(df)
        df = df.drop_duplicates(subset=subset, keep='first')
        n_after = len(df)
        n_removed = n_before - n_after
        
        if n_removed > 0:
            logger.warning(f"Removed {n_removed} duplicate rows")
        
        return df
    
    def preprocess(
        self, 
        df: pd.DataFrame,
        remove_prohibited: bool = True,
        validate: bool = True
    ) -> pd.DataFrame:
        """
        Run full preprocessing pipeline.
        
        Args:
            df: Input DataFrame
            remove_prohibited: Whether to remove prohibited columns
            validate: Whether to validate schema
            
        Returns:
            Preprocessed DataFrame
        """
        logger.info("Starting preprocessing pipeline")
        
        # Validate schema
        if validate:
            is_valid, errors = self.validate_schema(df)
            if not is_valid:
                raise ValueError(f"Schema validation failed: {errors}")
        
        # Check data quality
        quality_report = self.check_data_quality(df)
        logger.info(f"Data quality: {quality_report['n_rows']} rows, "
                   f"{quality_report['duplicates']} duplicates")
        
        # Remove duplicates
        df = self.remove_duplicates(df)
        
        # Remove prohibited columns
        if remove_prohibited:
            df = self.remove_prohibited_columns(df)
        
        # Handle missing values
        df = self.handle_missing_values(df, strategy="median")
        
        logger.info("Preprocessing complete")
        return df


def load_and_preprocess(
    filepath: str,
    config: Optional[Config] = None
) -> Tuple[pd.DataFrame, DataPreprocessor]:
    """
    Convenience function to load and preprocess data in one call.
    
    Args:
        filepath: Path to data file
        config: Configuration object
        
    Returns:
        Tuple of (preprocessed_df, preprocessor_instance)
    """
    preprocessor = DataPreprocessor(config)
    df = preprocessor.load_data(filepath)
    df_processed = preprocessor.preprocess(df)
    return df_processed, preprocessor
