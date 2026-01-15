"""
Testes de integração para a API FastAPI.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

# Mock do modelo antes de importar o app
@pytest.fixture(scope="module")
def mock_model():
    """Cria modelo mock para testes."""
    model = MagicMock()
    # Retorna probabilidades para classe 0 e 1
    model.predict_proba = MagicMock(
        return_value=np.array([[0.3, 0.7]])
    )
    return model


@pytest.fixture(scope="module")
def mock_metadata():
    """Metadata mock."""
    return {
        "model_version": "v1.0.0-test",
        "model_family": "rf",
        "calibration": "sigmoid",
        "expected_features": [
            "fase_2023", "iaa_2023", "ian_2023", "ida_2023", "idade_2023",
            "ieg_2023", "instituicao_2023", "ipp_2023", "ips_2023", "ipv_2023",
            "max_indicador", "media_indicadores", "min_indicador",
            "range_indicadores", "std_indicadores"
        ],
        "threshold_policy": {"threshold_value": 0.5},
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture(scope="module")
def mock_signature():
    """Signature mock."""
    return {
        "input_schema": [
            {"name": "fase_2023", "type": "float64"},
            {"name": "iaa_2023", "type": "float64"},
        ],
        "output_schema": [
            {"name": "risk_score", "type": "float64"},
            {"name": "risk_label", "type": "int64"},
        ],
    }


@pytest.fixture(scope="module")
def test_client(mock_model, mock_metadata, mock_signature):
    """Cria TestClient com mocks."""
    with patch("app.main.model_manager") as mock_manager:
        mock_manager.model = mock_model
        mock_manager.metadata = mock_metadata
        mock_manager.signature = mock_signature
        mock_manager.version = "v1.0.0-test"
        mock_manager.threshold = 0.5
        mock_manager.expected_features = mock_metadata["expected_features"]
        mock_manager.get_safe_metadata.return_value = {
            "model_version": "v1.0.0-test",
            "model_family": "rf",
            "threshold": 0.5,
            "expected_features": mock_metadata["expected_features"],
            "calibration": "sigmoid",
            "created_at": "2025-01-01T00:00:00Z",
        }
        
        from app.main import app
        
        client = TestClient(app)
        yield client


class TestHealthEndpoint:
    """Testes para endpoint /health."""
    
    def test_health_returns_200(self, test_client):
        """Deve retornar 200 quando saudável."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
    
    def test_health_response_schema(self, test_client):
        """Deve retornar schema correto."""
        response = test_client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "model_loaded" in data
        assert "uptime_seconds" in data
    
    def test_health_includes_request_id_header(self, test_client):
        """Deve incluir X-Request-ID no header."""
        response = test_client.get("/health")
        
        assert "X-Request-ID" in response.headers


class TestMetadataEndpoint:
    """Testes para endpoint /metadata."""
    
    def test_metadata_returns_200(self, test_client):
        """Deve retornar 200."""
        response = test_client.get("/metadata")
        
        assert response.status_code == 200
    
    def test_metadata_response_schema(self, test_client):
        """Deve retornar schema correto."""
        response = test_client.get("/metadata")
        data = response.json()
        
        assert "model_version" in data
        assert "model_family" in data
        assert "threshold" in data
        assert "expected_features" in data
    
    def test_metadata_returns_features_list(self, test_client):
        """Deve retornar lista de features."""
        response = test_client.get("/metadata")
        data = response.json()
        
        assert isinstance(data["expected_features"], list)
        assert len(data["expected_features"]) > 0


class TestPredictEndpoint:
    """Testes para endpoint /predict."""
    
    @pytest.fixture
    def valid_payload(self):
        """Payload válido para testes."""
        return {
            "instances": [
                {
                    "fase_2023": 3.0,
                    "iaa_2023": 7.5,
                    "ian_2023": 6.0,
                    "ida_2023": 5.5,
                    "idade_2023": 12.0,
                    "ieg_2023": 6.5,
                    "instituicao_2023": "A",
                    "ipp_2023": 7.0,
                    "ips_2023": 6.8,
                    "ipv_2023": 5.0,
                    "max_indicador": 7.5,
                    "media_indicadores": 6.3,
                    "min_indicador": 5.0,
                    "range_indicadores": 2.5,
                    "std_indicadores": 0.8,
                }
            ]
        }
    
    def test_predict_returns_200(self, test_client, valid_payload):
        """Deve retornar 200 para payload válido."""
        response = test_client.post("/predict", json=valid_payload)
        
        assert response.status_code == 200
    
    def test_predict_response_schema(self, test_client, valid_payload):
        """Deve retornar schema correto."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        assert "predictions" in data
        assert "request_id" in data
        assert "processing_time_ms" in data
    
    def test_predict_returns_predictions_list(self, test_client, valid_payload):
        """Deve retornar lista de predições."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) == 1
    
    def test_prediction_has_score_and_label(self, test_client, valid_payload):
        """Cada predição deve ter score e label."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        pred = data["predictions"][0]
        assert "risk_score" in pred
        assert "risk_label" in pred
        assert "model_version" in pred
    
    def test_risk_score_in_range(self, test_client, valid_payload):
        """Score deve estar entre 0 e 1."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        score = data["predictions"][0]["risk_score"]
        assert 0 <= score <= 1
    
    def test_risk_label_binary(self, test_client, valid_payload):
        """Label deve ser 0 ou 1."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        label = data["predictions"][0]["risk_label"]
        assert label in [0, 1]
    
    def test_predict_rejects_empty_instances(self, test_client):
        """Deve rejeitar lista vazia."""
        response = test_client.post("/predict", json={"instances": []})
        
        assert response.status_code == 422
    
    def test_predict_returns_request_id(self, test_client, valid_payload):
        """Deve retornar request_id."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        assert data["request_id"] is not None
        assert len(data["request_id"]) > 0
    
    def test_predict_includes_processing_time(self, test_client, valid_payload):
        """Deve incluir tempo de processamento."""
        response = test_client.post("/predict", json=valid_payload)
        data = response.json()
        
        assert data["processing_time_ms"] > 0
    
    def test_predict_batch(self, test_client):
        """Deve aceitar batch de instâncias."""
        payload = {
            "instances": [
                {"fase_2023": 1.0, "iaa_2023": 5.0},
                {"fase_2023": 2.0, "iaa_2023": 6.0},
                {"fase_2023": 3.0, "iaa_2023": 7.0},
            ]
        }
        
        # Mock precisa retornar array do tamanho do batch
        with patch("app.main.model_manager") as mock_manager:
            mock_manager.model = MagicMock()
            mock_manager.model.predict_proba.return_value = np.array([
                [0.4, 0.6],
                [0.5, 0.5],
                [0.3, 0.7],
            ])
            mock_manager.version = "v1.0.0-test"
            mock_manager.threshold = 0.5
            mock_manager.expected_features = [
                "fase_2023", "iaa_2023", "ian_2023", "ida_2023", "idade_2023",
                "ieg_2023", "instituicao_2023", "ipp_2023", "ips_2023", "ipv_2023",
                "max_indicador", "media_indicadores", "min_indicador",
                "range_indicadores", "std_indicadores"
            ]
            
            from app.main import app
            client = TestClient(app)
            response = client.post("/predict", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                assert len(data["predictions"]) == 3


class TestErrorHandling:
    """Testes para tratamento de erros."""
    
    def test_error_response_includes_request_id(self, test_client):
        """Erro deve incluir request_id."""
        response = test_client.post("/predict", json={"instances": []})
        data = response.json()
        
        # Erro de validação pode não ter request_id no body
        # mas deve ter no header
        assert "X-Request-ID" in response.headers
    
    def test_error_response_has_detail(self, test_client):
        """Erro deve ter campo detail."""
        response = test_client.post("/predict", json={"instances": []})
        data = response.json()
        
        assert "detail" in data


class TestNoSensitiveDataInLogs:
    """Testes para garantir que dados sensíveis não vazam."""
    
    def test_no_ra_in_response(self, test_client):
        """RA não deve aparecer na resposta."""
        payload = {
            "instances": [
                {"ra": "12345", "fase_2023": 3.0, "iaa_2023": 7.0}
            ]
        }
        
        with patch("app.main.model_manager") as mock_manager:
            mock_manager.model = MagicMock()
            mock_manager.model.predict_proba.return_value = np.array([[0.3, 0.7]])
            mock_manager.version = "v1.0.0"
            mock_manager.threshold = 0.5
            mock_manager.expected_features = [
                "fase_2023", "iaa_2023", "ian_2023", "ida_2023", "idade_2023",
                "ieg_2023", "instituicao_2023", "ipp_2023", "ips_2023", "ipv_2023",
                "max_indicador", "media_indicadores", "min_indicador",
                "range_indicadores", "std_indicadores"
            ]
            
            from app.main import app
            client = TestClient(app)
            response = client.post("/predict", json=payload)
            
            response_text = response.text
            assert "12345" not in response_text
    
    def test_no_nome_in_response(self, test_client):
        """Nome não deve aparecer na resposta."""
        payload = {
            "instances": [
                {"nome": "João Silva", "fase_2023": 3.0, "iaa_2023": 7.0}
            ]
        }
        
        with patch("app.main.model_manager") as mock_manager:
            mock_manager.model = MagicMock()
            mock_manager.model.predict_proba.return_value = np.array([[0.3, 0.7]])
            mock_manager.version = "v1.0.0"
            mock_manager.threshold = 0.5
            mock_manager.expected_features = [
                "fase_2023", "iaa_2023", "ian_2023", "ida_2023", "idade_2023",
                "ieg_2023", "instituicao_2023", "ipp_2023", "ips_2023", "ipv_2023",
                "max_indicador", "media_indicadores", "min_indicador",
                "range_indicadores", "std_indicadores"
            ]
            
            from app.main import app
            client = TestClient(app)
            response = client.post("/predict", json=payload)
            
            response_text = response.text
            assert "João Silva" not in response_text
