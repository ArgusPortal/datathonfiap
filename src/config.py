"""Configuration management for the ML pipeline."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Global configuration for the project."""
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_RAW_DIR = DATA_DIR / "raw"
    DATA_PROCESSED_DIR = DATA_DIR / "processed"
    MODELS_DIR = PROJECT_ROOT / "models"
    NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
    
    # Model settings
    TARGET_COLUMN = "em_risco_t_mais_1"
    RANDOM_STATE = 42
    TEST_SIZE = 0.2
    
    # Feature engineering
    TEMPORAL_HORIZON = "t_to_t_plus_1"  # t -> t+1
    MIN_HISTORY_YEARS = 1  # Minimum years of history needed
    
    # Training
    MODEL_TYPE = "random_forest"  # or "xgboost", "logistic_regression"
    METRIC_PRIMARY = "recall"  # Primary metric for optimization
    METRIC_SECONDARY = "pr_auc"  # Secondary metric for evaluation
    RECALL_TARGET = 0.75  # Target recall for MVP
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    MODEL_PATH = PROJECT_ROOT / "app" / "model" / "model.pkl"
    
    # Data quality thresholds
    MAX_MISSING_CRITICAL = 0.0  # % missing for critical features (IDs, target)
    MAX_MISSING_ACADEMIC = 0.2  # % missing for academic features
    MAX_MISSING_ENGAGEMENT = 0.3  # % missing for engagement features
    
    # Leakage prevention
    PROHIBITED_COLUMNS = [
        "estudante_id",
        "nome",
        "cpf",
        "turma_id",
        "escola_id",
    ]
    
    LEAKAGE_WATCHLIST = [
        "fase_efetiva_t_mais_1",
        "fase_ideal_t_mais_1",
        "status_matricula_t_mais_1",
        "notas_parciais_t_mais_1",
    ]
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_data_path(cls, filename: str, processed: bool = False) -> Path:
        """Get full path for a data file."""
        base_dir = cls.DATA_PROCESSED_DIR if processed else cls.DATA_RAW_DIR
        return base_dir / filename
    
    @classmethod
    def get_model_path(cls, model_name: Optional[str] = None) -> Path:
        """Get full path for a model file."""
        if model_name is None:
            model_name = "model.pkl"
        return cls.MODELS_DIR / model_name
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories if they don't exist."""
        for dir_path in [
            cls.DATA_RAW_DIR,
            cls.DATA_PROCESSED_DIR,
            cls.MODELS_DIR,
            cls.NOTEBOOKS_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Create directories on import
Config.ensure_dirs()
