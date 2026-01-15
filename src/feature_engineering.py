"""Feature engineering module."""

import logging
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np

from .config import Config

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Handles feature engineering and transformation."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.feature_names = []
        
    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temporal features (deltas, trends).
        
        NOTE: This is a placeholder. Real implementation requires
        longitudinal data with multiple years per student.
        
        Args:
            df: Input DataFrame with temporal structure
            
        Returns:
            DataFrame with temporal features added
        """
        logger.info("Creating temporal features (placeholder)")
        
        # Placeholder: these would require actual multi-year data
        # Example features to create:
        # - delta_inde_t_vs_t1: INDE change year-over-year
        # - delta_ian_t_vs_t1: IAN change year-over-year
        # - tendencia_notas: slope of grades over time
        
        # For now, create dummy features to demonstrate structure
        if 'inde_ano_t' in df.columns:
            df['inde_squared'] = df['inde_ano_t'] ** 2
            
        if 'ian_ano_t' in df.columns:
            df['ian_squared'] = df['ian_ano_t'] ** 2
        
        # TODO: implement real temporal features when multi-year data is available
        
        return df
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between key variables.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with interaction features added
        """
        logger.info("Creating interaction features")
        
        # Academic performance x engagement
        if 'inde_ano_t' in df.columns and 'taxa_presenca_ano_t' in df.columns:
            df['inde_x_presenca'] = df['inde_ano_t'] * df['taxa_presenca_ano_t']
        
        if 'ian_ano_t' in df.columns and 'taxa_presenca_ano_t' in df.columns:
            df['ian_x_presenca'] = df['ian_ano_t'] * df['taxa_presenca_ano_t']
        
        # Academic indicators interaction
        if 'inde_ano_t' in df.columns and 'ian_ano_t' in df.columns:
            df['inde_x_ian'] = df['inde_ano_t'] * df['ian_ano_t']
        
        return df
    
    def create_aggregation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create aggregation features (by phase, by vulnerability level, etc.).
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with aggregation features added
        """
        logger.info("Creating aggregation features")
        
        # Example: mean encoding by program phase (with regularization to avoid leakage)
        if 'fase_programa' in df.columns and 'inde_ano_t' in df.columns:
            # Global mean for smoothing
            global_mean = df['inde_ano_t'].mean()
            
            # Group statistics
            phase_stats = df.groupby('fase_programa')['inde_ano_t'].agg(['mean', 'count'])
            
            # Smoothed mean (to avoid overfitting on small groups)
            smoothing_factor = 10
            phase_stats['smoothed_mean'] = (
                (phase_stats['mean'] * phase_stats['count'] + global_mean * smoothing_factor) /
                (phase_stats['count'] + smoothing_factor)
            )
            
            # Map back to dataframe
            df['inde_mean_by_fase'] = df['fase_programa'].map(phase_stats['smoothed_mean'])
        
        return df
    
    def create_risk_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create explicit risk indicator features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with risk indicators added
        """
        logger.info("Creating risk indicators")
        
        # Low attendance flag
        if 'taxa_presenca_ano_t' in df.columns:
            df['baixa_presenca'] = (df['taxa_presenca_ano_t'] < 0.75).astype(int)
        
        # Low academic performance flag
        if 'inde_ano_t' in df.columns:
            # TODO: confirm INDE threshold for "low performance" from PEDE documentation
            df['baixo_inde'] = (df['inde_ano_t'] < 5.0).astype(int)
        
        if 'ian_ano_t' in df.columns:
            # TODO: confirm IAN threshold for "low performance"
            df['baixo_ian'] = (df['ian_ano_t'] < 5.0).astype(int)
        
        # Combined risk flag
        if 'baixa_presenca' in df.columns and 'baixo_inde' in df.columns:
            df['multiplos_riscos'] = (
                (df['baixa_presenca'] == 1) & (df['baixo_inde'] == 1)
            ).astype(int)
        
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode categorical features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with categorical features encoded
        """
        logger.info("Encoding categorical features")
        
        # Phase is already numeric (0-7), but ensure it's treated as ordinal
        if 'fase_programa' in df.columns:
            df['fase_programa'] = df['fase_programa'].astype(int)
        
        # If there are other categorical columns, handle them here
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_cols:
            if col != self.config.TARGET_COLUMN:
                # One-hot encode (for nominal) or label encode (for ordinal)
                # For now, use one-hot encoding
                logger.info(f"One-hot encoding: {col}")
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                df = pd.concat([df, dummies], axis=1)
                df = df.drop(columns=[col])
        
        return df
    
    def select_features(
        self, 
        df: pd.DataFrame,
        feature_list: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Select specific features for modeling.
        
        Args:
            df: Input DataFrame
            feature_list: List of feature names to keep. If None, keep all except target.
            
        Returns:
            DataFrame with selected features only
        """
        if feature_list is not None:
            # Keep only specified features
            available_features = [f for f in feature_list if f in df.columns]
            missing_features = [f for f in feature_list if f not in df.columns]
            
            if missing_features:
                logger.warning(f"Requested features not found: {missing_features}")
            
            df = df[available_features]
            logger.info(f"Selected {len(available_features)} features")
        else:
            # Keep all except target and IDs
            exclude_cols = [self.config.TARGET_COLUMN] + self.config.PROHIBITED_COLUMNS
            feature_cols = [col for col in df.columns if col not in exclude_cols]
            df = df[feature_cols]
        
        self.feature_names = df.columns.tolist()
        return df
    
    def engineer_features(
        self,
        df: pd.DataFrame,
        include_temporal: bool = True,
        include_interactions: bool = True,
        include_aggregations: bool = True,
        include_risk_indicators: bool = True
    ) -> pd.DataFrame:
        """
        Run full feature engineering pipeline.
        
        Args:
            df: Input DataFrame (after preprocessing)
            include_temporal: Whether to create temporal features
            include_interactions: Whether to create interaction features
            include_aggregations: Whether to create aggregation features
            include_risk_indicators: Whether to create risk indicator features
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Starting feature engineering pipeline")
        
        df = df.copy()
        
        if include_temporal:
            df = self.create_temporal_features(df)
        
        if include_interactions:
            df = self.create_interaction_features(df)
        
        if include_aggregations:
            df = self.create_aggregation_features(df)
        
        if include_risk_indicators:
            df = self.create_risk_indicators(df)
        
        # Encode categorical features
        df = self.encode_categorical_features(df)
        
        logger.info(f"Feature engineering complete. Total features: {len(df.columns)}")
        
        return df


def create_features(
    df: pd.DataFrame,
    config: Optional[Config] = None
) -> Tuple[pd.DataFrame, FeatureEngineer]:
    """
    Convenience function to create features in one call.
    
    Args:
        df: Preprocessed DataFrame
        config: Configuration object
        
    Returns:
        Tuple of (df_with_features, feature_engineer_instance)
    """
    engineer = FeatureEngineer(config)
    df_features = engineer.engineer_features(df)
    return df_features, engineer
