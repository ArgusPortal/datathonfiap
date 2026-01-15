"""Smoke tests to verify basic functionality."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path


def test_config_imports():
    """Test that config module can be imported."""
    from src.config import Config
    
    config = Config()
    assert config.RANDOM_STATE == 42
    assert config.TARGET_COLUMN == "em_risco_t_mais_1"
    assert config.RECALL_TARGET == 0.75


def test_preprocessing_imports():
    """Test that preprocessing module can be imported."""
    from src.preprocessing import DataPreprocessor
    
    preprocessor = DataPreprocessor()
    assert preprocessor is not None


def test_feature_engineering_imports():
    """Test that feature engineering module can be imported."""
    from src.feature_engineering import FeatureEngineer
    
    engineer = FeatureEngineer()
    assert engineer is not None


def test_train_imports():
    """Test that train module can be imported."""
    from src.train import ModelTrainer
    
    trainer = ModelTrainer()
    assert trainer is not None


def test_evaluate_imports():
    """Test that evaluate module can be imported."""
    from src.evaluate import ModelEvaluator
    
    evaluator = ModelEvaluator()
    assert evaluator is not None


def test_preprocessing_basic_functionality():
    """Test basic preprocessing functionality with dummy data."""
    from src.preprocessing import DataPreprocessor
    from src.config import Config
    
    # Create dummy data
    df = pd.DataFrame({
        'inde_ano_t': [5.0, 6.0, 4.5, 7.0],
        'ian_ano_t': [4.0, 5.5, 3.5, 6.0],
        'taxa_presenca_ano_t': [0.8, 0.9, 0.7, 0.95],
        'fase_programa': [2, 3, 1, 4],
        'em_risco_t_mais_1': [0, 0, 1, 0]
    })
    
    config = Config()
    preprocessor = DataPreprocessor(config)
    
    # Test quality check
    quality_report = preprocessor.check_data_quality(df)
    assert quality_report['n_rows'] == 4
    assert quality_report['n_columns'] == 5
    assert quality_report['target_missing'] == 0


def test_feature_engineering_basic_functionality():
    """Test basic feature engineering functionality with dummy data."""
    from src.feature_engineering import FeatureEngineer
    
    # Create dummy data
    df = pd.DataFrame({
        'inde_ano_t': [5.0, 6.0, 4.5, 7.0],
        'ian_ano_t': [4.0, 5.5, 3.5, 6.0],
        'taxa_presenca_ano_t': [0.8, 0.9, 0.7, 0.95],
        'fase_programa': [2, 3, 1, 4],
        'em_risco_t_mais_1': [0, 0, 1, 0]
    })
    
    engineer = FeatureEngineer()
    df_features = engineer.engineer_features(df)
    
    # Check that features were created
    assert len(df_features.columns) > len(df.columns)
    
    # Check for expected interaction features
    assert 'inde_x_presenca' in df_features.columns
    assert 'ian_x_presenca' in df_features.columns


def test_model_evaluation_with_dummy_predictions():
    """Test model evaluation with dummy predictions."""
    from src.evaluate import ModelEvaluator
    
    # Dummy predictions
    y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 0])
    y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1, 1, 0])
    y_proba = np.array([0.2, 0.8, 0.4, 0.3, 0.9, 0.1, 0.85, 0.95, 0.6, 0.15])
    
    evaluator = ModelEvaluator()
    metrics = evaluator.evaluate(y_true, y_pred, y_proba)
    
    # Check that key metrics are present
    assert 'recall' in metrics
    assert 'precision' in metrics
    assert 'f1' in metrics
    assert 'roc_auc' in metrics
    assert 'pr_auc' in metrics
    assert 'confusion_matrix' in metrics


def test_api_health_endpoint():
    """Test API health endpoint."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'healthy'
    assert 'model_loaded' in data


def test_api_root_endpoint():
    """Test API root endpoint."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'version' in data


def test_api_predict_endpoint():
    """Test API predict endpoint with valid payload."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    payload = {
        "estudante_id": "test_001",
        "ano_base": 2024,
        "features": {
            "inde_ano_t": 5.5,
            "ian_ano_t": 4.8,
            "taxa_presenca_ano_t": 0.85,
            "fase_programa": 3
        }
    }
    
    response = client.post("/predict", json=payload)
    
    # Accept 200 (model loaded) or 503 (model not loaded yet - expected in Phase 0)
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert 'score' in data
        assert 'classe_predita' in data
        assert 'versao_modelo' in data
        assert 0.0 <= data['score'] <= 1.0
        assert data['classe_predita'] in [0, 1]


def test_api_predict_endpoint_validation():
    """Test API predict endpoint with invalid payload."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Invalid payload: missing required field
    payload = {
        "estudante_id": "test_001",
        "ano_base": 2024,
        "features": {
            "inde_ano_t": 5.5,
            # Missing ian_ano_t
            "taxa_presenca_ano_t": 0.85,
            "fase_programa": 3
        }
    }
    
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Validation error


def test_directories_exist():
    """Test that required directories exist."""
    from src.config import Config
    
    config = Config()
    
    # These should be created by Config.ensure_dirs()
    assert config.DATA_RAW_DIR.exists()
    assert config.DATA_PROCESSED_DIR.exists()
    assert config.MODELS_DIR.exists()
    assert config.NOTEBOOKS_DIR.exists()


def test_leakage_detection():
    """Test that leakage detection works."""
    from src.preprocessing import DataPreprocessor
    from src.config import Config
    
    # Create data with leakage column
    df = pd.DataFrame({
        'inde_ano_t': [5.0, 6.0],
        'fase_efetiva_t_mais_1': [1, 2],  # This is in leakage watchlist
        'em_risco_t_mais_1': [0, 1]
    })
    
    config = Config()
    preprocessor = DataPreprocessor(config)
    
    is_valid, errors = preprocessor.validate_schema(df)
    
    assert not is_valid
    assert any('leakage' in str(error).lower() for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
