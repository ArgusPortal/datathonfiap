"""
Testes para src/schema_validation.py.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSchemaValidation:
    """Testes para validação de schema."""
    
    @pytest.fixture
    def valid_inference_data(self):
        """Dados válidos para inferência."""
        return pd.DataFrame({
            "fase_2023": [3, 2, 4],
            "iaa_2023": [6.5, 7.0, 5.5],
            "ian_2023": [7.2, 6.8, 7.0],
            "ida_2023": [5.8, 6.0, 6.2],
            "idade_2023": [14, 12, 15],
            "ieg_2023": [6.0, 6.5, 5.5],
            "instituicao_2023": [1, 1, 2],
            "ipp_2023": [7.5, 7.0, 6.5],
            "ips_2023": [8.0, 7.5, 7.0],
            "ipv_2023": [6.2, 6.0, 6.5],
            "max_indicador": [8.0, 7.5, 7.5],
            "media_indicadores": [6.8, 6.5, 6.3],
            "min_indicador": [5.0, 5.5, 5.0],
            "range_indicadores": [3.0, 2.0, 2.5],
            "std_indicadores": [0.9, 0.7, 0.8]
        })
    
    @pytest.fixture
    def valid_training_data(self, valid_inference_data):
        """Dados válidos para treino (inclui target)."""
        df = valid_inference_data.copy()
        df["em_risco_2024"] = [0, 1, 0]  # Target correto
        return df
    
    def test_validate_inference_success(self, valid_inference_data):
        """Testa validação bem-sucedida de inferência."""
        from src.schema_validation import validate_input_schema
        
        # Não deve levantar exceção
        validate_input_schema(valid_inference_data, mode="inference")
    
    def test_validate_training_success(self, valid_training_data):
        """Testa validação bem-sucedida de treino."""
        from src.schema_validation import validate_training_data
        
        validate_training_data(valid_training_data)
    
    def test_missing_required_feature(self, valid_inference_data):
        """Testa erro quando feature obrigatória está faltando."""
        from src.schema_validation import validate_input_schema, SchemaValidationError
        
        df = valid_inference_data.drop(columns=["fase_2023"])
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_input_schema(df, mode="inference")
        
        assert "fase_2023" in str(exc_info.value)
    
    def test_extra_feature_rejected(self, valid_inference_data):
        """Testa erro quando feature extra não permitida."""
        from src.schema_validation import validate_input_schema, SchemaValidationError
        
        df = valid_inference_data.copy()
        df["extra_column"] = [1, 2, 3]
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_input_schema(df, mode="inference", extra_policy="reject")
        
        assert "extra" in str(exc_info.value).lower()
    
    def test_pii_field_rejected(self, valid_inference_data):
        """Testa erro quando campo PII está presente."""
        from src.schema_validation import validate_input_schema, SchemaValidationError
        
        df = valid_inference_data.copy()
        df["ra"] = ["12345", "67890", "11111"]  # PII field
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_input_schema(df, mode="inference")
        
        assert "pii" in str(exc_info.value).lower() or "ra" in str(exc_info.value).lower()
    
    def test_nome_pii_rejected(self, valid_inference_data):
        """Testa erro quando nome (PII) está presente."""
        from src.schema_validation import validate_input_schema, SchemaValidationError
        
        df = valid_inference_data.copy()
        df["nome"] = ["Alice", "Bob", "Carol"]
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_input_schema(df, mode="inference")
        
        assert "pii" in str(exc_info.value).lower() or "nome" in str(exc_info.value).lower()
    
    def test_missing_target_in_training(self, valid_inference_data):
        """Testa erro quando target está faltando no treino."""
        from src.schema_validation import validate_training_data, SchemaValidationError
        
        # valid_inference_data não tem target
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_training_data(valid_inference_data)
        
        assert "target" in str(exc_info.value).lower() or "em_risco" in str(exc_info.value).lower()
    
    def test_invalid_target_values(self, valid_training_data):
        """Testa erro quando target tem valores inválidos."""
        from src.schema_validation import validate_training_data, SchemaValidationError
        
        df = valid_training_data.copy()
        df.loc[0, "em_risco_2024"] = 5  # Deve ser 0 ou 1
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_training_data(df)
        
        assert "target" in str(exc_info.value).lower() or "binário" in str(exc_info.value).lower()
    
    def test_empty_batch(self):
        """Testa erro quando batch está vazio."""
        from src.schema_validation import validate_inference_batch, SchemaValidationError
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_inference_batch([])
        
        assert "vazio" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()


class TestInputSchemaDict:
    """Testes para validação de input como dict."""
    
    def test_validate_batch_success(self):
        """Testa validação de batch como lista de dicts."""
        from src.schema_validation import validate_inference_batch
        
        instances = [
            {
                "fase_2023": 3,
                "iaa_2023": 6.5,
                "ian_2023": 7.2,
                "ida_2023": 5.8,
                "idade_2023": 14,
                "ieg_2023": 6.0,
                "instituicao_2023": 1,
                "ipp_2023": 7.5,
                "ips_2023": 8.0,
                "ipv_2023": 6.2,
                "max_indicador": 8.0,
                "media_indicadores": 6.8,
                "min_indicador": 5.0,
                "range_indicadores": 3.0,
                "std_indicadores": 0.9
            }
        ]
        
        # Não deve levantar exceção
        validate_inference_batch(instances)
    
    def test_validate_batch_missing_field(self):
        """Testa erro quando campo obrigatório falta."""
        from src.schema_validation import validate_inference_batch, SchemaValidationError
        
        instances = [
            {
                "fase_2023": 3,
                # Faltando outras features
            }
        ]
        
        with pytest.raises(SchemaValidationError):
            validate_inference_batch(instances)


class TestSchemaValidationMessages:
    """Testes para mensagens de erro claras."""
    
    def test_error_message_includes_field_name(self):
        """Testa que mensagem de erro inclui nome do campo."""
        from src.schema_validation import validate_input_schema, SchemaValidationError
        
        df = pd.DataFrame({"wrong_field": [1, 2, 3]})
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_input_schema(df, mode="inference")
        
        error_msg = str(exc_info.value)
        # Deve mencionar campos faltantes
        assert len(error_msg) > 10  # Mensagem significativa
