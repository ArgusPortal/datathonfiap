"""
Testes unitários para módulo model_loader.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.model_loader import (
    ModelManager,
    load_json_file,
    load_metadata,
    load_model,
    load_signature,
)


class TestLoadJsonFile:
    """Testes para função load_json_file."""
    
    def test_load_valid_json(self, tmp_path):
        """Deve carregar JSON válido."""
        data = {"key": "value", "number": 42}
        json_path = tmp_path / "test.json"
        json_path.write_text(json.dumps(data))
        
        result = load_json_file(json_path)
        
        assert result == data
    
    def test_load_nonexistent_file(self, tmp_path):
        """Deve retornar None para arquivo inexistente."""
        result = load_json_file(tmp_path / "nonexistent.json")
        assert result is None
    
    def test_load_invalid_json(self, tmp_path):
        """Deve retornar None para JSON inválido."""
        json_path = tmp_path / "invalid.json"
        json_path.write_text("not valid json {")
        
        result = load_json_file(json_path)
        assert result is None


class TestLoadModel:
    """Testes para função load_model."""
    
    def test_load_valid_model(self, tmp_path):
        """Deve carregar modelo válido."""
        import joblib
        from sklearn.linear_model import LogisticRegression
        
        # Cria modelo real simples
        model = LogisticRegression()
        model_path = tmp_path / "model.joblib"
        joblib.dump(model, model_path)
        
        result = load_model(model_path)
        
        assert result is not None
    
    def test_load_nonexistent_model(self, tmp_path):
        """Deve retornar None para modelo inexistente."""
        result = load_model(tmp_path / "nonexistent.joblib")
        assert result is None
    
    def test_load_corrupted_model(self, tmp_path):
        """Deve retornar None para modelo corrompido."""
        model_path = tmp_path / "corrupted.joblib"
        model_path.write_text("not a valid model")
        
        result = load_model(model_path)
        assert result is None


class TestLoadMetadata:
    """Testes para função load_metadata."""
    
    def test_load_valid_metadata(self, tmp_path):
        """Deve carregar metadata válida."""
        metadata = {
            "model_version": "v1.0.0",
            "threshold_policy": {"threshold_value": 0.5},
        }
        path = tmp_path / "metadata.json"
        path.write_text(json.dumps(metadata))
        
        result = load_metadata(path)
        
        assert result == metadata
    
    def test_load_metadata_not_found(self, tmp_path):
        """Deve retornar None se não encontrar."""
        result = load_metadata(tmp_path / "nonexistent.json")
        assert result is None


class TestLoadSignature:
    """Testes para função load_signature."""
    
    def test_load_valid_signature(self, tmp_path):
        """Deve carregar signature válida."""
        signature = {
            "input_schema": [{"name": "feat1", "type": "float64"}],
            "output_schema": [{"name": "score", "type": "float64"}],
        }
        path = tmp_path / "signature.json"
        path.write_text(json.dumps(signature))
        
        result = load_signature(path)
        
        assert result == signature


class TestModelManager:
    """Testes para classe ModelManager."""
    
    @pytest.fixture
    def mock_artifacts(self, tmp_path):
        """Cria artefatos mock para testes."""
        import joblib
        from sklearn.linear_model import LogisticRegression
        
        # Modelo real simples
        model = LogisticRegression()
        model_path = tmp_path / "model.joblib"
        joblib.dump(model, model_path)
        
        # Metadata
        metadata = {
            "model_version": "v1.0.0",
            "model_family": "rf",
            "calibration": "sigmoid",
            "expected_features": ["feat1", "feat2"],
            "threshold_policy": {"threshold_value": 0.5},
            "created_at": "2025-01-01T00:00:00Z",
        }
        metadata_path = tmp_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata))
        
        # Signature
        signature = {
            "input_schema": [
                {"name": "feat1", "type": "float64"},
                {"name": "feat2", "type": "float64"},
            ],
            "output_schema": [{"name": "score", "type": "float64"}],
        }
        signature_path = tmp_path / "signature.json"
        signature_path.write_text(json.dumps(signature))
        
        return model_path, metadata_path, signature_path
    
    def test_load_all_artifacts(self, mock_artifacts):
        """Deve carregar todos os artefatos."""
        model_path, metadata_path, signature_path = mock_artifacts
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path)
        
        assert manager.model is not None
        assert manager.metadata is not None
        assert manager.signature is not None
    
    def test_version_property(self, mock_artifacts):
        """Deve retornar versão correta."""
        model_path, metadata_path, signature_path = mock_artifacts
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path)
        
        assert manager.version == "v1.0.0"
    
    def test_threshold_property(self, mock_artifacts):
        """Deve retornar threshold correto."""
        model_path, metadata_path, signature_path = mock_artifacts
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path)
        
        assert manager.threshold == 0.5
    
    def test_expected_features_property(self, mock_artifacts):
        """Deve retornar features esperadas."""
        model_path, metadata_path, signature_path = mock_artifacts
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path)
        
        assert manager.expected_features == ["feat1", "feat2"]
    
    def test_get_safe_metadata(self, mock_artifacts):
        """Deve retornar metadata segura (sem caminhos sensíveis)."""
        model_path, metadata_path, signature_path = mock_artifacts
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path)
        
        safe = manager.get_safe_metadata()
        
        assert "model_version" in safe
        assert "threshold" in safe
        assert "expected_features" in safe
        # Não deve conter caminhos
        assert "model_path" not in safe
    
    def test_default_threshold_when_missing(self, tmp_path):
        """Deve usar threshold padrão do config se não definido no metadata."""
        import joblib
        from sklearn.linear_model import LogisticRegression
        from app.config import DEFAULT_THRESHOLD
        
        model = LogisticRegression()
        model_path = tmp_path / "model.joblib"
        joblib.dump(model, model_path)
        
        # Metadata sem threshold_policy
        metadata = {"model_version": "v1.0.0"}
        metadata_path = tmp_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata))
        
        manager = ModelManager()
        manager.load(model_path, metadata_path)
        
        # Deve usar o DEFAULT_THRESHOLD do config.py (0.040)
        assert manager.threshold == DEFAULT_THRESHOLD
    
    def test_input_schema_property(self, mock_artifacts):
        """Deve retornar input schema."""
        model_path, metadata_path, signature_path = mock_artifacts
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path)
        
        schema = manager.input_schema
        
        assert len(schema) == 2
        assert schema[0]["name"] == "feat1"
    
    def test_load_without_signature(self, tmp_path):
        """Deve carregar mesmo sem signature."""
        import joblib
        from sklearn.linear_model import LogisticRegression
        
        model = LogisticRegression()
        model_path = tmp_path / "model.joblib"
        joblib.dump(model, model_path)
        
        metadata = {"model_version": "v1.0.0", "expected_features": ["f1"]}
        metadata_path = tmp_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata))
        
        manager = ModelManager()
        manager.load(model_path, metadata_path, signature_path=None)
        
        assert manager.model is not None
        assert manager._signature is None
    
    def test_raises_on_model_not_found(self, tmp_path):
        """Deve levantar erro se modelo não encontrado."""
        manager = ModelManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load(tmp_path / "nonexistent.joblib", tmp_path / "metadata.json")
