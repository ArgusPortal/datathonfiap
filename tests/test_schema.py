"""
Testes unitários para schemas e validação.
"""

import pytest

from app.schema import (
    PredictRequest,
    PredictResponse,
    PredictionResult,
    StudentFeatures,
    validate_batch_features,
    validate_features,
)


class TestStudentFeatures:
    """Testes para StudentFeatures schema."""
    
    def test_all_fields_optional(self):
        """Todos os campos devem ser opcionais."""
        features = StudentFeatures()
        
        assert features.iaa_2023 is None
        assert features.ian_2023 is None
    
    def test_accepts_valid_values(self):
        """Deve aceitar valores válidos."""
        features = StudentFeatures(
            iaa_2023=7.5,
            ian_2023=6.0,
            fase_2023=3.0,
        )
        
        assert features.iaa_2023 == 7.5
        assert features.ian_2023 == 6.0
    
    def test_allows_extra_fields(self):
        """Deve permitir campos extras (extra='allow')."""
        features = StudentFeatures(
            iaa_2023=7.5,
            extra_field="value",
        )
        
        assert features.iaa_2023 == 7.5


class TestPredictRequest:
    """Testes para PredictRequest schema."""
    
    def test_valid_request(self):
        """Deve aceitar request válido."""
        request = PredictRequest(
            instances=[{"feat1": 5.0, "feat2": 3.0}]
        )
        
        assert len(request.instances) == 1
    
    def test_rejects_empty_instances(self):
        """Deve rejeitar lista de instâncias vazia."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            PredictRequest(instances=[])
    
    def test_rejects_too_many_instances(self):
        """Deve rejeitar mais de 1000 instâncias."""
        with pytest.raises(ValueError, match="Máximo de 1000"):
            PredictRequest(instances=[{"feat1": 1.0}] * 1001)
    
    def test_accepts_batch(self):
        """Deve aceitar batch de instâncias."""
        request = PredictRequest(
            instances=[
                {"feat1": 1.0},
                {"feat1": 2.0},
                {"feat1": 3.0},
            ]
        )
        
        assert len(request.instances) == 3


class TestPredictionResult:
    """Testes para PredictionResult schema."""
    
    def test_valid_result(self):
        """Deve aceitar resultado válido."""
        result = PredictionResult(
            risk_score=0.75,
            risk_label=1,
            model_version="v1.0.0",
        )
        
        assert result.risk_score == 0.75
        assert result.risk_label == 1
        assert result.model_version == "v1.0.0"


class TestValidateFeatures:
    """Testes para função validate_features."""
    
    def test_valid_features(self):
        """Deve validar features corretas."""
        features = {"feat1": 5.0, "feat2": 3.0}
        expected = ["feat1", "feat2"]
        
        result = validate_features(features, expected)
        
        assert result == {"feat1": 5.0, "feat2": 3.0}
    
    def test_orders_features(self):
        """Deve ordenar features conforme expected."""
        features = {"feat2": 3.0, "feat1": 5.0}
        expected = ["feat1", "feat2"]
        
        result = validate_features(features, expected)
        
        # Verifica ordem das chaves
        assert list(result.keys()) == ["feat1", "feat2"]
    
    def test_fills_missing_with_none(self):
        """Deve preencher features faltantes com None."""
        features = {"feat1": 5.0}
        expected = ["feat1", "feat2"]
        
        result = validate_features(features, expected)
        
        assert result["feat1"] == 5.0
        assert result["feat2"] is None
    
    def test_rejects_extra_features(self):
        """Deve rejeitar features extras com policy='reject'."""
        features = {"feat1": 5.0, "extra": 99.0}
        expected = ["feat1"]
        
        with pytest.raises(ValueError, match="Features não esperadas"):
            validate_features(features, expected, extra_policy="reject")
    
    def test_ignores_extra_features(self):
        """Deve ignorar features extras com policy='ignore'."""
        features = {"feat1": 5.0, "extra": 99.0}
        expected = ["feat1"]
        
        result = validate_features(features, expected, extra_policy="ignore")
        
        assert result == {"feat1": 5.0}
        assert "extra" not in result
    
    def test_ignores_id_fields(self):
        """Deve ignorar campos de ID mesmo com policy='reject'."""
        features = {"feat1": 5.0, "ra": "12345", "id": "abc", "nome": "João"}
        expected = ["feat1"]
        
        result = validate_features(features, expected, extra_policy="reject")
        
        assert result == {"feat1": 5.0}
    
    def test_ignores_student_id(self):
        """Deve ignorar student_id e estudante_id."""
        features = {"feat1": 5.0, "student_id": "S001", "estudante_id": "E001"}
        expected = ["feat1"]
        
        result = validate_features(features, expected, extra_policy="reject")
        
        assert result == {"feat1": 5.0}


class TestValidateBatchFeatures:
    """Testes para função validate_batch_features."""
    
    def test_validate_batch(self):
        """Deve validar batch de instâncias."""
        instances = [
            {"feat1": 1.0, "feat2": 2.0},
            {"feat1": 3.0, "feat2": 4.0},
        ]
        expected = ["feat1", "feat2"]
        
        result = validate_batch_features(instances, expected)
        
        assert len(result) == 2
        assert result[0] == {"feat1": 1.0, "feat2": 2.0}
    
    def test_error_includes_instance_index(self):
        """Deve incluir índice da instância no erro."""
        instances = [
            {"feat1": 1.0},
            {"feat1": 2.0, "extra": 99.0},
        ]
        expected = ["feat1"]
        
        with pytest.raises(ValueError, match="Instância 1"):
            validate_batch_features(instances, expected, extra_policy="reject")
    
    def test_fills_missing_in_batch(self):
        """Deve preencher missing em todas as instâncias."""
        instances = [
            {"feat1": 1.0},
            {"feat2": 2.0},
        ]
        expected = ["feat1", "feat2"]
        
        result = validate_batch_features(instances, expected)
        
        assert result[0]["feat2"] is None
        assert result[1]["feat1"] is None
