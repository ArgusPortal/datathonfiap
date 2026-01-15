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
    from src.preprocessing import build_preprocessor, validate_no_blocked_columns, identify_column_types
    
    assert callable(build_preprocessor)
    assert callable(validate_no_blocked_columns)
    assert callable(identify_column_types)


def test_feature_engineering_imports():
    """Test that feature engineering module can be imported."""
    from src.feature_engineering import make_features, create_delta_features, create_risk_composites
    
    assert callable(make_features)
    assert callable(create_delta_features)
    assert callable(create_risk_composites)


def test_train_imports():
    """Test that train module can be imported."""
    from src.train import load_and_prepare_data, create_candidate_models, train_and_evaluate_v1, save_artifacts_v1
    
    assert callable(load_and_prepare_data)
    assert callable(create_candidate_models)
    assert callable(train_and_evaluate_v1)
    assert callable(save_artifacts_v1)


def test_evaluate_imports():
    """Test that evaluate module can be imported."""
    from src.evaluate import calculate_metrics, select_threshold, evaluate_predictions, compare_models
    
    assert callable(calculate_metrics)
    assert callable(select_threshold)
    assert callable(evaluate_predictions)
    assert callable(compare_models)


def test_preprocessing_basic_functionality():
    """Test basic preprocessing functionality with dummy data."""
    from src.preprocessing import build_preprocessor, identify_column_types
    
    # Create dummy data
    df = pd.DataFrame({
        'ian_2023': [5.0, 6.0, 4.5, 7.0],
        'ida_2023': [4.0, 5.5, 3.5, 6.0],
        'ieg_2023': [0.8, 0.9, 0.7, 0.95],
        'fase_2023': ['ALFA', 'F1', 'F2', 'F3'],
        'instituicao_2023': ['A', 'B', 'A', 'C'],
    })
    
    # Test building preprocessor
    preprocessor, num_cols, cat_cols = build_preprocessor(df, target_year=2024)
    assert preprocessor is not None
    assert len(num_cols) == 3  # ian, ida, ieg
    assert len(cat_cols) == 2  # fase, instituicao
    
    # Test identify_column_types
    numeric, categorical = identify_column_types(df)
    assert 'ian_2023' in numeric
    assert 'fase_2023' in categorical


def test_feature_engineering_basic_functionality():
    """Test basic feature engineering functionality with dummy data."""
    from src.feature_engineering import make_features, create_risk_composites
    
    # Create dummy data
    df = pd.DataFrame({
        'ian_2023': [5.0, 6.0, 4.5, 7.0],
        'ida_2023': [4.0, 5.5, 3.5, 6.0],
        'ieg_2023': [5.2, 6.3, 4.1, 7.5],
        'iaa_2023': [5.5, 6.0, 4.0, 7.2],
        'ips_2023': [5.1, 5.8, 4.2, 7.0],
        'ipp_2023': [4.8, 5.5, 4.3, 6.8],
        'ipv_2023': [5.0, 6.2, 4.5, 7.1],
        'fase_2023': ['ALFA', 'F1', 'F2', 'F3'],
    })
    
    df_features = make_features(df)
    
    # Check that composite features were created
    assert 'media_indicadores' in df_features.columns
    assert 'min_indicador' in df_features.columns
    assert 'std_indicadores' in df_features.columns
    
    # Check that original columns preserved
    assert 'ian_2023' in df_features.columns


def test_model_evaluation_with_dummy_predictions():
    """Test model evaluation with dummy predictions."""
    from src.evaluate import calculate_metrics, select_threshold
    
    # Dummy predictions
    y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 0])
    y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1, 1, 0])
    y_proba = np.array([0.2, 0.8, 0.4, 0.3, 0.9, 0.1, 0.85, 0.95, 0.6, 0.15])
    
    metrics = calculate_metrics(y_true, y_pred, y_proba)
    
    # Check that key metrics are present
    assert 'recall' in metrics
    assert 'precision' in metrics
    assert 'f1' in metrics
    assert 'pr_auc' in metrics
    assert 'confusion_matrix' in metrics
    
    # Test threshold selection
    threshold, th_metrics = select_threshold(y_true, y_proba, objective="max_recall")
    assert 0 <= threshold <= 1
    assert 'recall' in th_metrics


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
    from src.preprocessing import validate_no_blocked_columns, BLOCKED_COLUMNS
    import pytest
    
    # Create data with leakage column
    df = pd.DataFrame({
        'ian_2023': [5.0, 6.0],
        'em_risco_2024': [0, 1],  # This is a blocked column (target)
    })
    
    # Should raise error because em_risco is in blocked columns
    with pytest.raises(ValueError):
        validate_no_blocked_columns(df.columns.tolist(), target_year=2024)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
